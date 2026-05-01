import random

from .astnode import AstNode
from .error import EvaluatorError, TodoError
from .result import EvalResult


class Evaluator:  # 求值器：输入 AST，输出结果（包含中间过程）。
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        raise TodoError("Evaluator初始化")

    def eval(self, node: AstNode) -> EvalResult:
        raise TodoError("Evaluator进行求值")
