from mistake.parser.ast import ASTNode


class RuntimeError(Exception):
    def __init__(self, message, node: ASTNode | None = None):
        self.message = message
        self.node = node
        super().__init__(self.message)

class VariableNotFoundError(RuntimeError):
    pass


class VariableAlreadyDefinedError(RuntimeError):
    pass


class InvalidAssignmentError(RuntimeError):
    pass


class InvalidFunctionCallError(RuntimeError):
    pass


class InvalidLifetimeError(RuntimeError):
    pass


class LifetimeExpiredError(RuntimeError):
    pass


class StackEmptyError(RuntimeError):
    pass


class FileSwitchException(RuntimeError):
    pass


class RuntimeTypeError(RuntimeError):
    pass
