import sys
import time
import warnings
from collections.abc import Callable

gevent = None


from mistake import runner
from mistake.parser.ast import (
    ASTNode,
    Block,
    Boolean,
    ClassDefinition,
    ClassInstancing,
    FunctionApplication,
    FunctionDeclaration,
    JumpStatement,
    Match,
    MemberAccess,
    Number,
    String,
    Unit,
    UnparsedBody,
    VariableAccess,
    VariableDeclaration,
)
from mistake.parser.parser import Parser
from mistake.runtime.environment import ContextType, Environment
from mistake.runtime.errors.runtime_errors import RuntimeError
from mistake.runtime.runtime_types import (
    BuiltinFunction,
    ClassInstance,
    ClassType,
    Function,
    Lifetime,
    LifetimeType,
    MLCallable,
    MLType,
    RuntimeBoolean,
    RuntimeChannel,
    RuntimeNumber,
    RuntimeString,
    RuntimeUnit,
    get_timestamp,
)
from mistake.utils import to_decimal_seconds


def is_truthy(value: MLType) -> bool:
    if isinstance(value, RuntimeBoolean):
        return value.value
    return not isinstance(value, RuntimeUnit)


class Interpreter:
    def __init__(self, unsafe_mode=False):
        self.unsafe_mode = unsafe_mode
        self.parser = Parser()
        self.global_environment = Environment(None, context_type=ContextType.IMPURE)
        self.current_line = 1
        self.files: dict[str, List[ASTNode]] = {}
        self.tasks: List = []
        self.channel_id = 0
        self.current_line = 1
        self.lines_executed = 1
        self.print_callback: Callable[[MLType], None] = lambda x: None

    def print(self, value: MLType):
        print(value.to_string())
        self.print_callback(value)

    def _reset(self):
        self.global_environment = Environment(None, context_type=ContextType.IMPURE)
        self.current_line = 1
        self.files: dict[str, list[ASTNode]] = {}
        self.tasks: list = []
        self.channel_id = 0
        self.current_line = 1
        self.lines_executed = 1

    def create_channel(self, cb_s=lambda *_: None, cb_r=lambda: None):
        self.channel_id += 1
        return RuntimeChannel(self.channel_id, cb_s, cb_r)

    def send_to_channel(self, channel: RuntimeChannel, value: MLType):
        channel.send(value)
        return RuntimeUnit()

    def receive_from_channel(self, channel: RuntimeChannel):
        return channel.receive()

    def run_all_tasks(self):
        global gevent
        if not gevent:
            from gevent import monkey

            warnings.simplefilter("ignore", category=monkey.MonkeyPatchWarning) # Remove stupid monkey patch warning
            monkey.patch_all()

            import gevent as _g
            gevent = _g
        if self.tasks:
            # Run tasks asynchronously without blocking the main thread
            for task in self.tasks:
                task.start()
            self.tasks = [task for task in self.tasks if not task.ready()]

    def add_task(self, task):
        self.tasks.append(task)

    def visit_function_application(
        self,
        env: Environment,
        node: FunctionApplication,
        visit_arg: bool = True,
    ):
        param = self.visit_node(node.parameter, env) if visit_arg else node.parameter

        function = self.visit_node(node.called, env)

        is_builtin = False

        if not isinstance(function, Function):
            if not isinstance(function, BuiltinFunction) and not isinstance(
                function, MLCallable
            ):
                raise RuntimeError(
                    f"Called {node.called} is not a function, but a {type(function)}",
                    node.called
                )
            else:
                is_builtin = True

        if function.impure and env.context_type == ContextType.PURE:
            raise RuntimeError(
                f"Function {function} is impure and cannot be called in a pure context",
                node,
            )

        if is_builtin:
            try:
                result = function(param, env, self)
            except RuntimeError as e:
                raise RuntimeError(e.message, node)
            return result



        new_env = Environment(
            env,
            context_type=ContextType.IMPURE if function.impure else ContextType.PURE,
        )

        if function.captured_env is not None:
            new_env.absorb_environment(function.captured_env)
            new_env = Environment(
                new_env,
                context_type=ContextType.IMPURE
                if function.impure
                else ContextType.PURE,
            )

        new_env.add_variable(function.param, param, Lifetime(LifetimeType.INFINITE, 0))

        result = self.visit_node(self.get_function_body(function), new_env)
        return result

    def get_function_body(self, function: Function) -> ASTNode:
        if not isinstance(function.body, UnparsedBody):
            return function.body
        # Parsed on first call, then cached on the (shared) declaration body
        if function.body.parsed is None:
            function.body.parsed = Block(Parser().parse(function.body.tokens, throw=True))
        return function.body.parsed

    def visit_function_declaration(self, node: FunctionDeclaration, env: Environment):
        params = node.parameters

        cap_env = Environment(None, context_type=env.context_type)
        for var in env.get_all_defined_vars():
            value, life = env.get_full_var_data(var)
            cap_env.add_variable(
                var,
                value,
                life,
                ignore_duplicate=True,
            )

        # curry the function
        def get_curried(params, body):
            if len(params) == 1:
                return Function(
                    params[0],
                    body,
                    is_unparsed=isinstance(body, UnparsedBody),
                    raw_body=node.raw_body,
                    impure=node.impure,
                    captured_env=cap_env,
                )
            return Function(
                params[0],
                Block([get_curried(params[1:], body)]),
                is_unparsed=False,
                raw_body=node.raw_body,
                impure=node.impure,
                captured_env=cap_env,
            )

        r = get_curried(params, node.body)
        return r

    def visit_block(self, node: Block, env: Environment):
        new_env = Environment(env, context_type=env.context_type)
        if not node.body:
            return Unit()

        for statement in node.body[:-1]:
            self.visit_node(statement, new_env)

        return self.visit_node(node.body[-1], new_env)

    def get_lifetime(self, lifetime: str, *_):
        if lifetime == "inf":
            return Lifetime(LifetimeType.INFINITE, 0)

        lifetime_value = int(lifetime[:-1])
        lifetime_type = lifetime[-1]

        if lifetime_type == "l":
            return Lifetime(LifetimeType.LINES, lifetime_value, self.lines_executed)
        elif lifetime_type == "u":
            return Lifetime(LifetimeType.DMS_TIMESTAMP, lifetime_value, get_timestamp())
        elif lifetime_type == "t":
            return Lifetime(
                LifetimeType.TICKS, lifetime_value, time.process_time() * 20
            )
        elif lifetime_type == "s":
            return Lifetime(
                LifetimeType.DECIMAL_SECONDS,
                lifetime_value,
                to_decimal_seconds(time.process_time()),
            )
        else:
            raise RuntimeError(f"Invalid lifetime {lifetime}")

    def visit_class_definition(self, node: ClassDefinition, env: Environment):
        parent_class = None
        members = {}
        pmembers = set()
        if node.parent:
            parent_class = env.get_variable(node.parent, line=self.lines_executed)
            if not isinstance(parent_class, ClassType):
                raise RuntimeError(f"'{node.parent}' is not a valid class.", node)

            members = {name: value for name, value in parent_class.members.items()}
            pmembers = parent_class.public_members

        for name, value in node.members.items():
            members[name] = value

        pmembers.update(node.public_members)

        new_class = ClassType(members, pmembers)
        return new_class

    def visit_class_instancing(self, node: ClassInstancing, env: Environment):
        # Lookup the class in the environment
        class_type = env.get_variable(node.name, line=self.lines_executed)
        if not isinstance(class_type, ClassType):
            raise RuntimeError(f"'{node.name}' is not a valid class.", node)

        # Create a new instance with the class fields
        instance_members = {name: value for name, value in class_type.members.items()}

        instance_env = Environment(env, context_type=ContextType.IMPURE)
        for name, value in instance_members.items():
            v = self.visit_node(value, instance_env)
            if isinstance(v, Function):
                v.captured_env = instance_env
            instance_env.add_variable(
                name,
                v,
                Lifetime(LifetimeType.INFINITE, 0),
            )  # HACK: No lifetime handling for instance members because that's stupid

        return ClassInstance(class_type, instance_members, instance_env)

    def visit_member_access(self, node: MemberAccess, env: Environment):
        # Lookup the instance in the environment
        instance = self.visit_node(node.obj, env)

        if node.member == '"' and isinstance(instance, Function):
            return RuntimeString(instance.raw_body)

        if not isinstance(instance, ClassInstance):
            raise RuntimeError(f"'{node.obj}' is not a valid instance.", node)

        # Access the field of the instance
        if node.member not in instance.members:
            raise RuntimeError(f"'{node.member}' is not a valid field of '{node.obj}'.", node)
        if node.member not in instance.class_type.public_members:
            raise RuntimeError(
                f"'{node.member}' is not a public field of '{node.obj}'.",
                node
            )

        return instance.environment.get_variable(node.member, line=self.lines_executed)

    def visit_match(self, node: Match, env: Environment):
        expr = self.visit_node(node.expr, env)
        env.add_variable("@", expr, Lifetime(LifetimeType.INFINITE, 0))
        for case in node.cases:
            v = self.visit_node(case.condition, env)
            if not isinstance(v, RuntimeBoolean):
                raise RuntimeError(f"Match condition must be a boolean, got {v}", case)
            if is_truthy(v):
                return self.visit_node(case.expr, env)
        return self.visit_node(node.otherwise, env)

    def visit_node(self, node: ASTNode, env: Environment, imperative=False):
        if isinstance(node, Unit):
            return RuntimeUnit()
        if isinstance(node, Number):
            return RuntimeNumber(node.value)
        if isinstance(node, String):
            return RuntimeString(node.value)
        if isinstance(node, Boolean):
            return RuntimeBoolean(node.value)
        if isinstance(node, Function):
            return node
        if isinstance(node, VariableAccess):
            return env.get_variable(node.name, line=self.lines_executed)
        if isinstance(node, FunctionApplication):
            return self.visit_function_application(env, node)
        if isinstance(node, Block):
            return self.visit_block(node, env)
        if isinstance(node, VariableDeclaration):
            value = self.visit_node(node.value, env)
            env.add_variable(node.name, value, self.get_lifetime(node.lifetime, node))
            return value
        if isinstance(node, FunctionDeclaration):
            return self.visit_function_declaration(node, env)
        if isinstance(node, ClassDefinition):
            return self.visit_class_definition(node, env)
        if isinstance(node, ClassInstancing):
            return self.visit_class_instancing(node, env)
        if isinstance(node, MemberAccess):
            return self.visit_member_access(node, env)
        if isinstance(node, Match):
            return self.visit_match(node, env)
        if isinstance(node, JumpStatement):
            self.swap_file(
                self.visit_node(node.file_expr, env),
                self.visit_node(node.line_expr, env),
            )
            return Unit()
        raise NotImplementedError(f"Node {node} not implemented")

    def swap_file(self, filename: MLType, line: int):
        if isinstance(filename, RuntimeString):
            filename = filename.value
        else:
            raise RuntimeError(f"Expected string, got {filename}")

        if isinstance(line, RuntimeNumber):
            line = int(line.value)
        else:
            raise RuntimeError(f"Expected number, got {line}")

        if filename not in self.files:
            self.files[filename] = runner.fetch_file(filename)

        self.ast = self.files[filename]
        self.current_line = line - 1
        if self.current_line > len(self.ast):
            raise RuntimeError(f"Line {line} is out of bounds in file {filename}")

    def execute(
        self, ast: list[ASTNode], filename: str = "NO_FILE", standalone=False
    ) -> list[MLType]:
        self.ast = ast
        self.current_line = 1
        self.lines_executed = 1
        self.files[filename] = ast
        sys.setrecursionlimit(100000)

        result: list[MLType] = []

        while self.current_line <= len(self.ast):
            node = self.ast[self.current_line - 1]
            try:
                result.append(
                    self.visit_node(node, self.global_environment, imperative=True)
                )
                self.run_all_tasks()

            except RuntimeError as e:
                if self.unsafe_mode and not standalone:
                    raise e
                if not standalone:
                    if e.node is not None:
                        print(f"Error at => {e.node.to_string()}")
                    print(f"Error at line {self.current_line}, {e}")
                return result + [e]
            self.current_line += 1
            self.lines_executed += 1

        if gevent:
            gevent.joinall(self.tasks)
        return result
