import random

from . import astnode as ast
from .astnode import AstNode
from .error import DiceLangError, EvaluatorError, LexerError, ParserError, TodoError
from .evaluator import Evaluator
from .lexer import Lexer
from .parser import Parser


class Interpreter:
    context: dict[str, AstNode]
    lexer: Lexer
    parser: Parser
    evaluator: Evaluator

    def __init__(self, text: str, context: dict[str, AstNode] | None = None, rng: random.Random | None = None):
        self.context = context if context is not None else {}
        self.lexer = Lexer(text)
        self.parser = Parser(tokens=self.lexer.tokens)
        self.evaluator = Evaluator(rng=rng, context=self.context)

    def interpret(self):
        raise TodoError("Interpreter.interpret 尚未实现")

    def append(self, text: str):
        self.lexer.append(text)
        raise TodoError("Interpreter.append 尚未实现")

    def replace(self, text: str):
        self.lexer.replace(text)
        raise TodoError("Interpreter.replace 尚未实现")

    def __call__(self):
        raise TodoError("Interpreter.__call__ 尚未实现")

    def __iter__(self):
        raise TodoError("Interpreter.__iter__ 尚未实现")
