import random
from collections.abc import Generator

from . import astnode as ast
from .astnode import AstNode
from .error import DiceLangError, EvaluatorError, LexerError, ParserError, TodoError
from .evaluator import Evaluator
from .lexer import Lexer
from .parser import Parser
from .result import ErrorRes, ExprRes, MacroDefRes, Result, VarDefRes
from .statement import ErrorStmt, ExprStmt, MacroDefStmt, Statement, VarDefStmt
from .tokens import Token, TokenType


class Interpreter:
    parser: Parser
    evaluator: Evaluator
    buffer: list[Statement]

    def __init__(
        self,
        text: str,
        vars: dict[str, int] | None = None,
        macros: dict[str, AstNode] | None = None,
        rng: random.Random | None = None,
    ):
        self.vars = vars if vars is not None else {}
        self.macros = macros if macros is not None else {}
        self.parser = Parser()
        self.compile(text)
        self.evaluator = Evaluator(rng=rng, vars=self.vars, macros=self.macros)

    def compile(self, text: str):
        chunks: list[list[Token]] = []
        chunk: list[Token] = []
        for token in Lexer.tokenize(text):
            if token.type == TokenType.SEMICOLON:
                chunk.append(Token(TokenType.EOF, None, "EOF", -1))
                chunks.append(chunk)
                chunk = []
            else:
                chunk.append(token)
        chunks.append(chunk)
        statements: list[Statement] = []
        for chunk in chunks:
            if not chunk:
                continue
            stmt = self.parser.parse(tokens=chunk)
            statements.append(stmt)

        self.buffer = statements

        raise TodoError("Interpreter.compile 尚未实现")

    def interpret(self, stmt: Statement) -> Result:
        match stmt:
            case ErrorStmt():
                return ErrorRes(value=stmt.value)
        raise TodoError("Interpreter.interpret 尚未实现")

    def append(self, text: str):
        raise TodoError("Interpreter.append 尚未实现")

    def replace(self, text: str):
        raise TodoError("Interpreter.replace 尚未实现")

    def __call__(self):
        raise TodoError("Interpreter.__call__ 尚未实现")

    def __iter__(self) -> Generator[Result]:
        for stmt in self.buffer:
            yield self.interpret(stmt)
