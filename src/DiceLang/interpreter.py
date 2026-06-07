import random
from collections.abc import Generator

from .astnode import AstNode
from .error import LexerError
from .evaluator import Evaluator
from .lexer import Lexer
from .parser import Parser
from .result import ErrorRes, Result
from .statement import ErrorStmt, Statement
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
        self.buffer = self.compile(text)
        self.evaluator = Evaluator(rng=rng, vars=self.vars, macros=self.macros)

    def compile(self, text: str) -> list[Statement]:
        """编译文本，返回 Statement 列表。"""
        try:
            tokens = Lexer.tokenize(text)
        except LexerError as e:
            return [ErrorStmt(value=e)]

        # 按分号切分为多个语句块
        chunks: list[list[Token]] = []
        chunk: list[Token] = []
        for token in tokens:
            if token.type == TokenType.SEMICOLON:
                if chunk:
                    chunk.append(Token(TokenType.EOF, None, "EOF", -1))
                    chunks.append(chunk)
                chunk = []
            else:
                chunk.append(token)
        # 最后一个块：过滤掉纯 EOF 的空语句
        if chunk and not all(t.type == TokenType.EOF for t in chunk):
            chunks.append(chunk)

        # Parse 阶段：逐块解析（Parser.parse() 保证不抛异常）
        statements: list[Statement] = []
        for chunk in chunks:
            if not chunk:
                continue
            stmt = self.parser.parse(tokens=chunk)
            statements.append(stmt)
        return statements

    def interpret(self, stmt: Statement) -> Result:
        """
        对单条语句求值，总是返回 Result（永不抛异常）。
        ErrorStmt 直接短路为 ErrorRes，其余委托给 Evaluator.eval()。
        """
        if isinstance(stmt, ErrorStmt):
            return ErrorRes(value=stmt.value)
        return self.evaluator.eval(stmt)

    def append(self, text: str):
        """追加文本，编译后合并到现有缓冲区。返回 self 以便链式调用。"""
        self.buffer.extend(self.compile(text))
        return self

    def replace(self, text: str):
        """替换全部文本。返回 self 以便链式调用。"""
        self.buffer = self.compile(text)
        return self

    def __call__(self) -> list[Result]:
        """一次性返回所有语句的求值结果。"""
        return list(self)

    def __iter__(self) -> Generator[Result]:
        for stmt in self.buffer:
            yield self.interpret(stmt)
