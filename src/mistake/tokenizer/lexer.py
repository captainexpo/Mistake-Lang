from mistake.tokenizer.token import Token, TokenType
from mistake.utils import is_latin_alph
from typing import List
from mistake.parser.errors.parser_errors import ParserError
import re
import html

keywords_en: dict[str, TokenType] = {
    "variable": TokenType.KW_VARIABLE,
    "is": TokenType.KW_IS,
    "open": TokenType.KW_OPEN,
    "close": TokenType.KW_CLOSE,
    "impure": TokenType.KW_IMPURE,
    "function": TokenType.KW_FUNCTION,
    "end": TokenType.KW_END,
    "returns": TokenType.KW_RETURNS,
    "lifetime": TokenType.KW_LIFETIME,
    "true": TokenType.KW_TRUE,
    "false": TokenType.KW_FALSE,
    "public": TokenType.KW_PUBLIC,
    "randomize": TokenType.KW_RANDOMIZE,
    "type": TokenType.KW_TYPE,
    "number": TokenType.TYPE_NUMBER,
    "boolean": TokenType.TYPE_BOOLEAN,
    "unit": TokenType.KW_UNIT,
    "jump": TokenType.KW_JUMP,
    "new": TokenType.KW_NEW,
    "class": TokenType.KW_CLASS,
    "inherits": TokenType.KW_INHERITS,
    "has": TokenType.KW_HAS,
    "match": TokenType.KW_MATCH,
    "case": TokenType.KW_CASE,
    "cases": TokenType.KW_CASES,
    "otherwise": TokenType.KW_OTHERWISE,
    "member": TokenType.KW_MEMBER,
    "then": TokenType.KW_THEN,
    "of": TokenType.KW_OF,
    "do": TokenType.KW_DO,
    "use": TokenType.KW_USE,
    "from": TokenType.KW_FROM,
    "with": TokenType.KW_WITH,
    "comment": TokenType.EX_COMMENT,
    "string": TokenType.EX_STRING,
}
class Lexer:
    def __init__(self, keywords = keywords_en):
        self.errors: List[ParserError] = []
        self.tokens: List[Token] = []
        self.code = ""
        self.current_token = None
        self.current_position = 0
        self.current_line = 1
        self.keywords = keywords
        self.Q_keywords = {v:k for k, v in self.keywords.items()}

    def set_keywords(self, keywords):
        self.keywords = keywords
        self.Q_keywords = {v:k for k, v in self.keywords.items()}

    def add_token(self, token: Token):
        if token.type == TokenType.SYM_WHITESPACE and token.value == "":
            return
        self.tokens.append(token)

    def is_identifier(self, s: str) -> bool:
        contains_non_number = False
        for c in s:
            if not c.isdigit():
                contains_non_number = True
            if c.isalpha():
                return False
        return contains_non_number

    def get_token(self, s: str) -> TokenType:
        if s in self.keywords:
            return self.keywords[s]
        if re.fullmatch(r"\-?[0-9]+(\.[0-9]+)?", s) is not None:
            return TokenType.SYM_NUMBER
        if s[:-1].isdigit() and s[-1] in "lust":
            return TokenType.SYM_DURATION
        if self.is_identifier(s):
            return TokenType.SYM_IDENTIFIER

        return TokenType.ERROR

    def skip_whitespace(self):
        ws = ""
        while (
            self.current_position < len(self.code)
            and self.code[self.current_position].isspace()
        ):
            ws += self.code[self.current_position]
            if self.code[self.current_position] == "\n":
                self.current_line += 1
            self.current_position += 1
        if ws != "":
            self.add_token(Token(TokenType.SYM_WHITESPACE, ws, self.current_line))

    def skip_line(self):
        while (
            self.current_position < len(self.code)
            and self.code[self.current_position] != "\n"
        ):
            self.current_position += 1
        self.current_line += 1
        self.current_position += 1

    def get_string(self) -> str:
        start = self.current_position
        while (
            self.current_position < len(self.code)
            and self.code[self.current_position :].split(" ")[0] != self.Q_keywords[TokenType.KW_CLOSE]
        ):
            self.current_position += 1


        s = html.unescape(self.code[start + 1 : self.current_position - 1]).replace(
            "<br>", "\n"
        )
        return s

    def tokenize(self, code: str) -> List[Token]:
        self.code = code
        while self.current_position < len(self.code):
            self.skip_whitespace()
            if self.current_position >= len(self.code):
                break

            start = self.current_position
            while (
                self.current_position < len(self.code)
                and not self.code[self.current_position].isspace()
            ):
                self.current_position += 1

            t = self.code[start : self.current_position]

            token_type = self.get_token(t)
            if token_type == TokenType.EX_COMMENT:
                self.skip_line()
                continue

            if token_type == TokenType.EX_STRING:
                self.add_token(
                    Token(TokenType.SYM_STRING, self.get_string(), self.current_line)
                )
                continue

            if token_type == TokenType.ERROR:
                self.add_token(Token(TokenType.ERROR, t, self.current_line))
            else:
                self.add_token(Token(token_type, t, self.current_line))

        self.add_token(Token(TokenType.SYM_EOF, "EOF", self.current_line))

        # remove all prefix whitespace tokens
        while self.tokens[0].type == TokenType.SYM_WHITESPACE:
            self.tokens.pop(0)
        return self.tokens

    def __str__(self):
        return "\n".join([str(token) for token in self.tokens])

    def __repr__(self):
        return self.__str__()
