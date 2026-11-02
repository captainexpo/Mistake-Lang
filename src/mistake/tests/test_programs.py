import io
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from mistake.parser.parser import Parser
from mistake.runtime.errors.runtime_errors import RuntimeError as MLRuntimeError
from mistake.runtime.interpreter import Interpreter
from mistake.tokenizer.lexer import Lexer

EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "examples"

# Examples written in a non-English localization; these need a generated
# translation file (network access) so they are not parsed here.
LOCALIZED_EXAMPLES = {"fibonacci_zh.mistake"}


def parse(code: str):
    parser = Parser()
    ast = parser.parse(Lexer().tokenize(code))
    return ast, parser.errors


def run(code: str) -> list[str]:
    """Run a program and return the strings it printed."""
    ast, errors = parse(code)
    if errors:
        raise AssertionError(f"parse errors: {errors}")
    rt = Interpreter()
    printed: list[str] = []
    rt.print_callback = lambda v: printed.append(v.to_string())
    with redirect_stdout(io.StringIO()):
        results = rt.execute(ast, standalone=True)
    failures = [r for r in results if isinstance(r, MLRuntimeError)]
    if failures:
        raise AssertionError(f"runtime error: {failures[0]}")
    return printed


class TestExamplesParse(unittest.TestCase):
    def test_all_examples_parse(self):
        examples = sorted(EXAMPLES_DIR.glob("*.mistake"))
        self.assertTrue(examples, f"no examples found in {EXAMPLES_DIR}")
        for path in examples:
            if path.name in LOCALIZED_EXAMPLES:
                continue
            with self.subTest(example=path.name):
                _, errors = parse(path.read_text(encoding="utf-8"))
                self.assertEqual(errors, [])


class TestStringLiterals(unittest.TestCase):
    def test_close_at_end_of_line(self):
        self.assertEqual(run("?! string hi close\nend\n"), ["hi"])

    def test_close_inside_word_does_not_end_string(self):
        self.assertEqual(run("?! string enclosed closet close end"), ["enclosed closet"])

    def test_empty_string(self):
        self.assertEqual(run("?! string  close end"), [""])

    def test_line_numbers_count_newlines_inside_strings(self):
        tokens = Lexer().tokenize("?! string a\nb close end\n?! 1 end")
        self.assertEqual(tokens[-1].line, 3)

    def test_long_string_lexes_in_linear_time(self):
        code = "?! string " + "x " * 80000 + " close end"
        start = time.perf_counter()
        Lexer().tokenize(code)
        self.assertLess(time.perf_counter() - start, 2.0)


class TestMatch(unittest.TestCase):
    def test_consecutive_matches_in_same_scope(self):
        code = (
            "?! match 1 cases case = @ 1 then string one close close otherwise 0 close close end\n"
            "?! match 2 cases case = @ 2 then string two close close otherwise 0 close close end\n"
        )
        self.assertEqual(run(code), ["one", "two"])


class TestUse(unittest.TestCase):
    def test_use_callback_is_callable(self):
        code = (
            "variable #1 is impure function ^1 returns ^1 5 close end\n"
            "use ^9 from #1 do ?! ^9 end\n"
        )
        self.assertEqual(run(code), ["5.0"])  # all numbers are floats


if __name__ == "__main__":
    unittest.main()
