from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv

from mistake import localize
from mistake.parser.parser import Parser
from mistake.runtime.environment import test
from mistake.runtime.interpreter import Interpreter
from mistake.tokenizer.lexer import Lexer

ENV_PATH = None


def print_help():
    print(
        "Usage: mistake-lang <filename> [--time] [--tokens] [--ast] [--no-exe] [--env <path>] [--vulkan]"
    )

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MistakeLang Interpreter")
    parser.add_argument("filename", type=str, help="The script file to run")
    parser.add_argument("--time", action="store_true", help="Print timing information")
    parser.add_argument("--tokens", action="store_true", help="Print tokens")
    parser.add_argument("--ast", action="store_true", help="Print AST")
    parser.add_argument(
        "--no-exe", action="store_true", help="Do not execute the script"
    )
    parser.add_argument("--env", type=str, help="Path to the .env file")
    parser.add_argument("--vulkan", action="store_true", help="Enable Vulkan support")
    parser.add_argument("--unsafe", action="store_true", help="Enable unsafe mode")
    parser.add_argument(
        "--end-env", action="store_true", help="Print the global environment at the end"
    )
    parser.add_argument(
        "--language",
        type=str,
        help='Language for localization, use lang = "purge" to purge all localizations',
    )
    parser.add_argument(
        "--env-tree", action="store_true", help="Print the environment tree"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.filename):
        print(f"File '{args.filename}' not found")
        sys.exit(1)

    return args


def run_script(
    program: str, lex=None, parser=None, rt=None, standalone=True
) -> tuple[bool, list | Any]:
    if lex is None:
        lex = Lexer()
    if parser is None:
        parser = Parser()
    if rt is None:
        rt = Interpreter(unsafe_mode=True)

    tokens = lex.tokenize(program)
    ast = parser.parse(tokens)
    if parser.errors:
        return (False, parser.errors)
    try:
        exe = rt.execute(ast, standalone=standalone)
        return (True, exe)
    except Exception as e:
        return (False, str(e))


def get_system_language() -> str:
    return os.getenv("LANG", "en").split(".")[0]

def graph_env_relations():
    graph = {}  # {parent: [children]}
    for env in test:
        graph[str(id(env))[-4:]] = []

    for env in test:
        if env.parent:
            graph[str(id(env.parent))[-4:]].append(env.repr_simple())

    return graph


def main():
    global ENV_PATH
    args = get_args()
    p_time = args.time

    cur_path = os.path.dirname(os.path.abspath(__file__))

    lexer = Lexer()
    parser = Parser()
    runtime = Interpreter(args.unsafe)

    lang = args.language if args.language is not None else get_system_language()
    if lang == "purge":
        localize.purge_localizations()
        return
    file = os.path.join(cur_path, f"./tokenizer/.localizations/{lang}.json")
    if not os.path.isfile(file):
        print(f"Localization file for {lang} not found, generating new translation.")
        localize.translate(lang)

    with open(file, "r", encoding="utf-8") as f:
        translate = json.loads(f.read())
        trans, keywords = translate.keys(), translate.values()
        n = {}
        for t, kw in zip(trans, keywords):
            n[t] = lexer.keywords[kw]

        lexer.set_keywords(n)

    ENV_PATH = args.env
    if ENV_PATH is not None:
        load_dotenv(ENV_PATH)
    else:
        load_dotenv()

    with open(args.filename, "r", encoding="utf-8") as f:
        if p_time:
            print("Read file:", time.process_time())
        start = time.time()

        os.chdir(os.path.dirname(os.path.abspath(args.filename)))
        code = f.read()

        tokens = lexer.tokenize(code)
        if p_time:
            print("Tokenized:", time.process_time())

        if args.tokens:
            print(tokens)

        ast = parser.parse(tokens)
        if p_time:
            print("Parsed:", time.process_time())

        if parser.errors:
            for error in parser.errors:
                print(error)
            return

        if args.ast:
            print("AST BEGIN")
            for i in ast:
                print(i)
            print("AST END")

        if not args.no_exe:
            runtime.execute(ast, filename=args.filename)

        if args.end_env:
            print(runtime.global_environment)

        if p_time:
            print(f"Total runtime: {time.time() - start} seconds")

        if args.env_tree:
            print(json.dumps(graph_env_relations(), indent=3))


if __name__ == "__main__":
    main()
