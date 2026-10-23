from typing import List


class ASTNode:
    def __init__(self):
        pass

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return self.__str__()

    def to_string(self):
        return self.__str__()


class VariableAccess(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"VariableAccess({self.name})"


class FunctionApplication(ASTNode):
    def __init__(self, called: ASTNode, parameter: ASTNode):
        self.called = called
        self.parameter = parameter

    def __str__(self):
        return f"FunctionApplication({self.called}, {self.parameter})"


class Number(ASTNode):
    def __init__(self, value: float):
        self.value = float(value)

    def __str__(self):
        return str(self.value)


class String(ASTNode):
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value


class Boolean(ASTNode):
    def __init__(self, value: bool):
        self.value = value

    def __str__(self):
        return str(self.value)


class Unit(ASTNode):
    def __init__(self):
        pass

    def __str__(self):
        return "Unit"


class Block(ASTNode):
    def __init__(self, body: List[ASTNode]):
        self.body = body

    def __str__(self):
        return f"Block({self.body})"


class VariableDeclaration(ASTNode):
    def __init__(
        self, name: str, value: ASTNode, lifetime: str = "inf", public: bool = False
    ):
        self.name = name
        self.value = value
        self.lifetime = lifetime
        self.public = public

    def __str__(self):
        return f"VariableDeclaration({self.name}, value={self.value}, lifetime={self.lifetime}, public={self.public})"


class FunctionDeclaration(ASTNode):
    def __init__(
        self, parameters: List[str], body: ASTNode, impure: bool = False, raw_body: str=""
    ):
        self.parameters = parameters
        self.body = body
        self.impure = impure
        self.raw_body = raw_body
    def __str__(self):
        return f"FunctionDeclaration({self.parameters}, body={self.body}, impure={self.impure})"


class UnparsedBody(ASTNode):
    """Function body tokens, parsed the first time the function is called."""

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.parsed: ASTNode | None = None

    def __str__(self):
        return f"UnparsedBody({''.join(str(t.value) for t in self.tokens)!r})"


class MatchCase(ASTNode):
    def __init__(self, condition: ASTNode, expr: ASTNode):
        self.condition = condition
        self.expr = expr

    def __str__(self):
        return f"MatchCase({self.condition}, {self.expr})"


class Match(ASTNode):
    def __init__(self, expr: ASTNode, cases: List[MatchCase], otherwise: ASTNode):
        self.expr = expr
        self.cases = cases
        self.otherwise = otherwise

    def __str__(self):
        return f"Match({self.expr}, cases={self.cases}, otherwise={self.otherwise})"


class ClassDefinition(ASTNode):
    def __init__(
        self,
        members: dict[str, ASTNode],
        parent: str | None = None,
        pmembers: set[str] = set(),
    ):
        self.members = members
        self.parent = parent
        self.public_members = pmembers

    def __str__(self):
        return f"ClassDefinition({self.members}, inherit={self.parent})"


class MemberAccess(ASTNode):
    def __init__(self, obj: str, member: str):
        self.obj = obj
        self.member = member

    def __str__(self):
        return f"MemberAccess({self.obj}, {self.member})"


class ClassInstancing(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"ClassInstance({self.name})"


class JumpStatement(ASTNode):
    def __init__(self, file_expr: ASTNode, line_expr: ASTNode):
        self.file_expr = file_expr
        self.line_expr = line_expr

    def __str__(self):
        return f"JumpStatement({self.file_expr}, {self.line_expr})"
