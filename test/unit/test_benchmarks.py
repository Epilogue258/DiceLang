import pytest

from DiceLang.evaluator import Evaluator
from DiceLang.lexer import Lexer
from DiceLang.parser import Parser


@pytest.fixture
def evaluator():
    return Evaluator()


@pytest.fixture
def ast_medium():
    """一个中等复杂度的表达式 AST"""
    source = "1 + 2*3 + 4d6 + (5+6)*7 + 2**3**2"
    tokens = Lexer.tokenize(source)
    return Parser(tokens).ast


def test_simplify_benchmark(benchmark, evaluator, ast_medium):
    # benchmark 会将内部函数执行多轮并统计
    result = benchmark(lambda: list(evaluator.eval(ast_medium)))
    assert len(result) > 0


def test_parse_benchmark(benchmark):
    source = "1 + 2*3 + 4d6 + (5+6)*7 + 2**3**2 + 1000d1000"
    tokens = Lexer.tokenize(source)
    result = benchmark(lambda: Parser(tokens).ast)
    assert result is not None
