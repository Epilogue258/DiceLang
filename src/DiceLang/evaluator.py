import random

import astnode
from astnode import AstNode, DiceResult


class Evaluator:  # 求值器：输入 AST，输出结果（包含中间过程）。
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        pass

    def eval(self, node: AstNode) -> DiceResult:  # TODO type hint在这里标红, 这不是错误, 只是因为之后再实现这里的pass
        pass
