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
        # Lex 阶段：捕获词法错误
        try:
            tokens = Lexer.tokenize(text)
        except LexerError as e:
            self.buffer = [ErrorStmt(value=e)]
            return

        # 按分号切分为多个语句块
        chunks: list[list[Token]] = []
        chunk: list[Token] = []
        for token in tokens:
            if token.type == TokenType.SEMICOLON:
                chunk.append(Token(TokenType.EOF, None, "EOF", -1))
                chunks.append(chunk)
                chunk = []
            else:
                chunk.append(token)
        # 最后一个块：过滤掉纯 EOF 的空语句（由尾随分号或连续分号产生）
        if chunk and not all(t.type == TokenType.EOF for t in chunk):
            chunks.append(chunk)

        # Parse 阶段：逐块解析（Parser.parse() 保证不抛异常，总是返回 Statement）
        statements: list[Statement] = []
        for chunk in chunks:
            if not chunk:
                continue
            stmt = self.parser.parse(tokens=chunk)
            statements.append(stmt)

        self.buffer = statements

    def interpret(self, stmt: Statement) -> Result:
        """
        对单条语句求值，总是返回 Result（永不抛异常）。
        ErrorStmt 直接短路为 ErrorRes，其余委托给 Evaluator.evaluate()。
        """
        if isinstance(stmt, ErrorStmt):
            return ErrorRes(value=stmt.value)
        return self.evaluator.evaluate(stmt.value)

    def append(self, text: str):
        raise TodoError("Interpreter.append 尚未实现")

    def replace(self, text: str):
        raise TodoError("Interpreter.replace 尚未实现")

    def __call__(self):
        raise TodoError("Interpreter.__call__ 尚未实现")

    def __iter__(self) -> Generator[Result]:
        for stmt in self.buffer:
            yield self.interpret(stmt)
