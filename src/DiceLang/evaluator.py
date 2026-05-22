import random
from typing import Any

import DiceLang.astnode as ast

from .astnode import AstNode, BinaryOpNode, NumberNode
from .error import EvaluatorError, TodoError
from .tokens import TokenType

# from .result import EvalResult


class Evaluator:  # 求值器：输入 AST，输出结果（包含中间过程）。
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def same_family(self, father: AstNode, children: list[AstNode]) -> bool:
        """判断一组节点是否均属于同一运算家族（例如都是加法、或者都是乘法）。"""
        return all((child.family & father.family) for child in children)

    def fold(self, node: AstNode, children: list[Any]) -> AstNode:
        """
        def fold
            case plus：
                return a + b
            case other op
                ...
        """
        match node:
            case BinaryOpNode():
                match node.op:
                    case TokenType.PLUS:
                        return NumberNode(value=children[0].value + children[1].value)
                    case TokenType.MINUS:
                        return NumberNode(value=children[0].value - children[1].value)
                    case TokenType.MULTIPLY:
                        return NumberNode(value=children[0].value * children[1].value)
                    case TokenType.DIVIDE:
                        return NumberNode(value=children[0].value // children[1].value)
                    case TokenType.POW:
                        return NumberNode(value=children[0].value ** children[1].value)
            case ast.DiceNode():
                # TODO 骰子展开，考虑selectors
                count = children[0].value
                sides = children[1].value
                rolls = [self.rng.randint(1, sides) for _ in range(count)]
                return NumberNode(value=sum(rolls))
            case _:
                raise EvaluatorError(f"Unsupported node for folding: {node}")
        raise TodoError("Evaluator.fold")

    def simplify(self, node: Any) -> AstNode:
        """
        def simplifier
        if all_child_num(sim_child) and samefam:
            return fold(node,sim_child)
        else
            return node(sim_child)
        """
        if not isinstance(node, AstNode):
            return node  # 不是AstNode的原子元素直接返回
        if isinstance(node, NumberNode):
            return node
        # object是为了兼容一些非AstNode的属性，例如SelectorNode中的selector, 但不至于用Any导致类型检查失效, 应该不算非常fancy的操作
        simlified_attr: list[AstNode | object] = [self.simplify(child) for child in node]
        simlified_child = [child for child in simlified_attr if isinstance(child, AstNode)]
        # 其实我想用filter的, 但是filter无法收窄类型检查, 刚好列表推导式看着也更好懂。
        if all(isinstance(child, NumberNode) for child in simlified_child) and self.same_family(node, node.children):
            return self.fold(node, simlified_child)
        return type(node).reconstruct(node, simlified_attr)

    def eval(self, node: AstNode):
        """
        求值器主函数，输入 AST，输出一个生成器，依次产出每一步化简的结果字符串。

        index 0 是原式，最后一个是最终结果。
        index n刚好是第n步化简的结果。
        """
        yield str(node)
        while not isinstance(node, NumberNode):
            node = self.simplify(node)
            yield str(node)


if __name__ == "__main__":
    # 简单测试
    from .lexer import Lexer
    from .parser import Parser

    source = "1+1 + 2*2"
    lex = Lexer(source)
    tokens = lex.tokens
    print(f"Tokens: {lex}")
    asttree = Parser(tokens).ast
    print(f"AST: {asttree}")
    evaluator = Evaluator()
    index = 0
    for step in evaluator.eval(asttree):
        print(f"Step {index}: {step}")
        index += 1


def recursive_map(func, data, condition):  # TODO
    """
    递归遍历嵌套列表，对满足 condition 的原子元素应用 func。
    """
    if isinstance(data, list):
        return [recursive_map(func, item, condition) for item in data]
    else:
        return func(data) if condition(data) else data
