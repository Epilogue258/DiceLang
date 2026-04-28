import random

from . import astnode
from .astnode import AstNode, DiceResult
from .error import EvaluatorError, TodoError


class Evaluator:  # 求值器：输入 AST，输出结果（包含中间过程）。
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        raise TodoError("Evaluator初始化")

    def eval(self, node: AstNode) -> DiceResult:  # TODO type hint在这里标红, 这不是错误, 只是因为之后再实现这里的pass
        raise TodoError("Evaluator进行求值")
