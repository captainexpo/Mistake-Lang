import unittest
from mistake.runtime.interpreter import Interpreter
from mistake.runtime.environment import Environment
from mistake.runtime.runtime_types import RuntimeNumber, RuntimeString, RuntimeBoolean, RuntimeUnit, Function

from mistake.parser.ast import (
    Number,
    String,
    Boolean,
    FunctionDeclaration,
    FunctionApplication,
    VariableDeclaration,
    VariableAccess,
    Block,
    Unit,
)

def reset_wrapper(func):
    def wrapper(self, *args, **kwargs):
        self.interpreter._reset()
        return func(self, *args, **kwargs)
    return wrapper

class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    @reset_wrapper
    def test_visit_number(self):
        node = Number(42)
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeNumber)
        self.assertEqual(result.value, 42)

    @reset_wrapper
    def test_visit_string(self):
        node = String("hello")
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeString)
        self.assertEqual(result.value, "hello")

    @reset_wrapper
    def test_visit_boolean(self):
        node = Boolean(True)
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeBoolean)
        self.assertEqual(result.value, True)

    @reset_wrapper
    def test_visit_unit(self):
        node = Unit()
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeUnit)

    @reset_wrapper
    def test_visit_variable_declaration(self):
        node = VariableDeclaration("x", Number(10), "inf")
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeNumber)
        self.assertEqual(result.value, 10)
        self.assertEqual(self.interpreter.global_environment.get_variable("x").value, 10)

    @reset_wrapper
    def test_visit_variable_access(self):
        self.interpreter.global_environment.add_variable("x", RuntimeNumber(10), self.interpreter.get_lifetime("inf"))
        node = VariableAccess("x")
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeNumber)
        self.assertEqual(result.value, 10)

    @reset_wrapper
    def test_visit_function_declaration(self):
        node = FunctionDeclaration("f", ["x"], Block([Number(42)]), False)
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, Function)

    @reset_wrapper
    def test_visit_function_application(self):
        func_decl = FunctionDeclaration(["x"], Block([VariableAccess("x")]), impure=True, raw_body="x")
        func = self.interpreter.visit_function_declaration(func_decl, Environment(None))
        self.interpreter.global_environment.add_variable("f", func, self.interpreter.get_lifetime("inf"))
        node = FunctionApplication(VariableAccess("f"), Number(10))
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeNumber)
        self.assertEqual(result.value, 10)

    @reset_wrapper
    def test_visit_block(self):
        node = Block([VariableDeclaration("x", Number(10), "inf"), VariableAccess("x")])
        result = self.interpreter.visit_node(node, self.interpreter.global_environment)
        self.assertIsInstance(result, RuntimeNumber)
        self.assertEqual(result.value, 10)

    @reset_wrapper
    def test_execute(self):
        ast = [VariableDeclaration("x", Number(10), "inf"), VariableAccess("x")]
        result = self.interpreter.execute(ast)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[1], RuntimeNumber)
        self.assertEqual(result[1].value, 10)

if __name__ == "__main__":
    unittest.main()
