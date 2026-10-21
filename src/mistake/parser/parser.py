from __future__ import annotations
from typing import Optional

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
    MatchCase,
    MemberAccess,
    Number,
    String,
    Unit,
    UnparsedBody,
    VariableAccess,
    VariableDeclaration,
)
from mistake.parser.errors.parser_errors import ParserError, UnexpectedTokenError
from mistake.tokenizer.lexer import Lexer
from mistake.tokenizer.token import Token, TokenType, opening_tokens


class Parser:
    breaking_tokens = [
        TokenType.KW_END,
        TokenType.KW_CLOSE,
        TokenType.SYM_EOF,
        TokenType.KW_CASES,
        TokenType.KW_THEN,
        TokenType.KW_OF,
        TokenType.KW_DO,
        TokenType.KW_FROM,
    ]

    def __init__(self):
        self.tokens = []
        self.position = 0
        self.current_token: Token = None
        self.errors: list[ParserError] = []

    def get_current(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        raise ParserError("Unexpected end of input")

    def parse(self, tokens: list[Token], throw=False) -> list[ASTNode]:
        self.tokens = tokens

        self.position = 0
        self.current_token = self.get_current()

        return self.parse_program(throw=throw)

    def synchronize(self):
        while self.current_token.type not in self.breaking_tokens:
            self.advance()

    def parse_program(self, throw=False) -> list[ASTNode]:
        nodes = []
        while self.current_token.type != TokenType.SYM_EOF:
            try:
                nodes.append(self.parse_node())
            except (ParserError, UnexpectedTokenError) as e:
                if throw:
                    raise e

                self.errors.append(e)
                try:
                    self.advance()
                    self.synchronize()
                except ParserError:
                    raise UnexpectedTokenError(
                        f"Unexpected token {self.current_token} at line {self.current_token.line}"
                    )
        return nodes

    def eat(self, token_type: TokenType):
        start = self.position
        if self.current_token.type == token_type:
            self.advance()
            return self.tokens[start]
        else:
            raise UnexpectedTokenError(
                f"Unexpected token {self.current_token} at line {self.current_token.line}, expected {token_type}"
            )

    def advance(self, allow_ws=False):
        self.position += 1
        while self.get_current().type == TokenType.SYM_WHITESPACE and not allow_ws:
            self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.get_current()

    def peek_next_is(self, token_type: TokenType):
        return self.tokens[self.position + 1].type == token_type

    def next_is(self, token_type: TokenType):
        return self.current_token.type == token_type

    def parse_node(self, require_end=True):
        if self.current_token.type in [TokenType.KW_PUBLIC, TokenType.KW_VARIABLE]:
            val = self.parse_variable_declaration()
        elif self.current_token.type == TokenType.KW_JUMP:
            val = self.parse_jump_statement()
        else:
            val = self.parse_expression()
        if require_end:
            self.eat(TokenType.KW_END)
        return val

    def parse_single_expr(self, atom: ASTNode, allow_function_application=True):
        if (
            self.current_token.type in self.breaking_tokens
            or not allow_function_application
        ):
            return atom

        return self.parse_function_application(atom)

    def parse_expression(self, allow_function_application=True):
        match self.current_token.type:
            case TokenType.SYM_NUMBER:
                val = Number(self.eat(TokenType.SYM_NUMBER).value)
            case TokenType.SYM_STRING:
                val = String(self.eat(TokenType.SYM_STRING).value)
                self.eat(TokenType.KW_CLOSE)
            case TokenType.KW_TRUE:
                self.eat(TokenType.KW_TRUE)
                val = Boolean(True)
            case TokenType.KW_FALSE:
                self.eat(TokenType.KW_FALSE)
                val = Boolean(False)
            case TokenType.KW_UNIT:
                self.eat(TokenType.KW_UNIT)
                val = Unit()
            case TokenType.SYM_IDENTIFIER:
                val = self.parse_id_expression(
                    allow_function_application=allow_function_application
                )
            case TokenType.KW_OPEN:
                val = self.parse_block()
            case TokenType.KW_FUNCTION:
                val = self.parse_function_declaration()
            case TokenType.KW_IMPURE:
                val = self.parse_function_declaration()
            case TokenType.KW_MATCH:
                val = self.parse_match_expression()
            case TokenType.KW_CLASS:
                val = self.parse_class_definition()
            case TokenType.KW_MEMBER:
                val = self.parse_member_access()
            case TokenType.KW_NEW:
                val = self.parse_class_instancing()
            case TokenType.KW_USE:
                val = self.parse_use()
            case TokenType.KW_WITH:
                val = self.parse_with()
            case _:
                raise UnexpectedTokenError(
                    f"Unexpected token {self.current_token} at line {self.current_token.line}"
                )

        return self.parse_single_expr(
            val, allow_function_application=allow_function_application
        )

    def parse_variable_declaration(self):
        public = False
        if self.next_is(TokenType.KW_PUBLIC):
            self.eat(TokenType.KW_PUBLIC)
            public = True
        self.eat(TokenType.KW_VARIABLE)
        name = self.eat(TokenType.SYM_IDENTIFIER).value
        if self.next_is(TokenType.KW_TYPE):
            self.eat(TokenType.KW_TYPE)
            self.advance()
        lifetime = "inf"
        if self.next_is(TokenType.KW_LIFETIME):
            self.eat(TokenType.KW_LIFETIME)
            lifetime = self.eat(TokenType.SYM_DURATION).value

        self.eat(TokenType.KW_IS)
        value = self.parse_expression()
        return VariableDeclaration(name, value, lifetime, public)

    def parse_case(self):
        self.eat(TokenType.KW_CASE)
        condition = self.parse_expression()
        self.eat(TokenType.KW_THEN)
        body = self.parse_expression()
        self.eat(TokenType.KW_CLOSE)
        return MatchCase(condition, body)

    def parse_match_expression(self):
        # match <expression> cases [case <expression> then <expression> close]mistake..? otherwise <expression> close close

        self.eat(TokenType.KW_MATCH)
        expr = self.parse_expression()
        self.eat(TokenType.KW_CASES)
        cases = []
        while self.current_token.type != TokenType.KW_OTHERWISE:
            cases.append(self.parse_case())

        self.eat(TokenType.KW_OTHERWISE)
        otherwise = self.parse_expression()
        self.eat(TokenType.KW_CLOSE)
        self.eat(TokenType.KW_CLOSE)
        return Match(expr, cases, otherwise)

    def get_unparsed_body(self):
        body: list[Token] = []
        stack = 1
        while stack > 0:
            if self.current_token.type in opening_tokens:
                stack += 1
            if self.current_token.type == TokenType.KW_CLOSE:
                stack -= 1
            if stack == 0:
                break

            body.append(self.current_token)
            self.advance(allow_ws=True)

        raw_body = "".join(str(t.value) for t in body).strip()

        if body[0].type != TokenType.KW_OPEN:
            body = (
                [Token(TokenType.KW_OPEN, "open")]
                + body
                + [Token(TokenType.KW_CLOSE, "close")]
            )

        result = body + [Token(TokenType.KW_END, "end"), Token(TokenType.SYM_EOF, "eof")]
        return result, raw_body

    def parse_class_definition(self):
        self.eat(TokenType.KW_CLASS)
        inherit = None
        if self.next_is(TokenType.KW_INHERITS):
            self.eat(TokenType.KW_INHERITS)
            inherit = self.eat(TokenType.SYM_IDENTIFIER).value
        self.eat(TokenType.KW_HAS)

        members = {}
        pmembers: set[str] = set()
        body: list[VariableDeclaration] = []
        while self.current_token.type != TokenType.KW_CLOSE:
            fucker = self.parse_variable_declaration()
            body.append(fucker)
            if fucker.public:
                pmembers.add(fucker.name)
            self.eat(TokenType.KW_END)

        for member in body:
            members[member.name] = member.value

        self.eat(TokenType.KW_CLOSE)
        return ClassDefinition(members, inherit, pmembers)

    def parse_member_access(self):
        self.eat(TokenType.KW_MEMBER)
        member = self.eat(TokenType.SYM_IDENTIFIER).value
        self.eat(TokenType.KW_OF)
        obj = self.parse_expression()
        return MemberAccess(obj, member)

    def parse_function_declaration(self):
        impure = False
        if self.next_is(TokenType.KW_IMPURE):
            self.eat(TokenType.KW_IMPURE)
            impure = True

        self.eat(TokenType.KW_FUNCTION)
        parameters = []
        while self.current_token.type != TokenType.KW_RETURNS:
            parameters.append(self.eat(TokenType.SYM_IDENTIFIER).value)

        self.eat(TokenType.KW_RETURNS)

        # Per the spec, the body is only parsed when the function is called
        body, raw_body = self.get_unparsed_body()
        self.eat(TokenType.KW_CLOSE)

        def get_curried_function(params: list[str], body: ASTNode):
            if not params:
                return body
            return FunctionDeclaration(
                [params[0]],
                get_curried_function(params[1:], body),
                impure=impure,
                raw_body=raw_body,
            )

        return get_curried_function(parameters, UnparsedBody(body))

    def parse_use(self):
        self.eat(TokenType.KW_USE)
        parameters: list[str] = []
        while self.current_token.type != TokenType.KW_FROM:
            parameters.append(self.eat(TokenType.SYM_IDENTIFIER).value)
        self.eat(TokenType.KW_FROM)
        call_expr = self.parse_expression()
        self.eat(TokenType.KW_DO)
        body_expr = self.parse_expression()

        callback = FunctionDeclaration(
            parameters, [Block([body_expr])], impure=True
        )
        return FunctionApplication(call_expr, callback)

    def parse_with(self):
        self.eat(TokenType.KW_WITH)
        raw = [self.parse_expression()]
        while self.current_token.type != TokenType.KW_CLOSE:
            self.eat(TokenType.KW_DO)
            raw.append(self.parse_expression())
        self.eat(TokenType.KW_CLOSE)

        def build_nested_call(exprs: list[ASTNode]):
            if len(exprs) == 1:
                return exprs[0]
            return FunctionApplication(exprs.pop(-1), build_nested_call(exprs))

        res = build_nested_call(raw.copy())

        return res

    def parse_id_expression(self, allow_function_application=True):
        if (
            self.tokens[self.position + 1].type not in self.breaking_tokens
            and allow_function_application
        ):
            return self.parse_function_application(
                VariableAccess(self.eat(TokenType.SYM_IDENTIFIER).value)
            )

        return VariableAccess(self.eat(TokenType.SYM_IDENTIFIER).value)

    def get_function_application_from_params(
        self, expr: ASTNode, params: list[ASTNode]
    ):
        for param in params:
            expr = FunctionApplication(expr, param)
        return expr

    def parse_function_application(self, func: ASTNode = None):
        parameters = []

        while self.current_token.type not in self.breaking_tokens:
            parameters.append(self.parse_expression(allow_function_application=False))

        return self.get_function_application_from_params(func, parameters)

    def parse_block(self):
        self.eat(TokenType.KW_OPEN)
        body = []
        while self.current_token.type != TokenType.KW_CLOSE:
            r = self.parse_node(False)
            body.append(r)
            if self.current_token.type == TokenType.KW_CLOSE:
                break
            self.eat(TokenType.KW_END)
        self.eat(TokenType.KW_CLOSE)
        return Block(body)

    def parse_class_instancing(self):
        self.eat(TokenType.KW_NEW)
        name = self.eat(TokenType.SYM_IDENTIFIER).value
        return ClassInstancing(name)

    def parse_jump_statement(self):
        self.eat(TokenType.KW_JUMP)
        line = self.parse_expression()
        self.eat(TokenType.KW_OF)
        file = self.parse_expression()
        return JumpStatement(file, line)


def get_file_ast(file: str) -> list[ASTNode]:
    with open(file) as f:
        code = f.read()
        lexer = Lexer()
        parser = Parser()
        tokens = lexer.tokenize(code)
        ast = parser.parse(tokens)
        return ast
