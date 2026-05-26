import random
from typing import Any

import DiceLang.astnode as ast

from .astnode import AstNode, BinaryOpNode, NumberNode
from .error import EvaluatorError, TodoError
from .statement import ExprStmt
from .tokens import TokenType

# from .result import EvalResult


class Evaluator:  # 求值器：输入 AST，输出结果（包含中间过程）。
    def __init__(
        self, rng: random.Random | None = None, vars: dict[str, int] | None = None, macros: dict[str, AstNode] | None = None
    ):
        self.rng = rng or random.Random()
        self.context = vars if vars is not None else {}
        self.macros = macros if macros is not None else {}

    def same_family(self, father: AstNode, children: list[AstNode]) -> bool:
        """判断一组节点是否均属于同一运算家族（例如都是加法、或者都是乘法）。"""
        res_family = father.family
        for child in children:
            res_family &= child.family
        return bool(res_family)

    def fold(self, node: AstNode, children: list[Any]) -> AstNode:
        """
        在所有子节点都抵达终点的前提下，根据父节点类型进行计算，返回一个新的结果。
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
                        if children[1].value != 0:
                            return NumberNode(value=children[0].value // children[1].value)
                        else:
                            raise EvaluatorError("除数不能为零", node=node)
                    case TokenType.POW:
                        return NumberNode(value=children[0].value ** children[1].value)
                    case TokenType.MOD:
                        return NumberNode(value=children[0].value % children[1].value)
                    case _:  # pragma: no cover
                        raise EvaluatorError(f"不支持的二元运算符: {node.op}", node=node)
            case ast.UnaryOpNode():
                match node.op:
                    case TokenType.PLUS:
                        return NumberNode(value=children[0].value)
                    case TokenType.MINUS:
                        return NumberNode(value=-children[0].value)
                    case _:  # pragma: no cover
                        raise EvaluatorError(f"不支持的一元运算符: {node.op}", node=node)
            case ast.GroupNode():
                return children[0]  # 直接返回唯一的子节点
            case ast.DiceNode():
                count = children[0].value
                sides = children[1].value
                rolls: list[int] = [self.rng.randint(1, sides) for _ in range(count)]
                return ast.DiceResNode(rolls=rolls, selectors=node.selectors)  # TODO selectors
            case ast.DiceResNode():
                # TODO selectors
                return NumberNode(value=sum(node.rolls))
            case _:  # pragma: no cover
                raise EvaluatorError(f"无法折叠的节点: {node}", node=node)

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
        simlified_child: list[AstNode] = [child for child in simlified_attr if isinstance(child, AstNode)]
        # 其实我想用filter的, 但是filter无法收窄类型检查, 刚好列表推导式看着也更好懂。
        if (
            all(isinstance(child, NumberNode) for child in simlified_child)  # all([]) == True
            and self.same_family(node, node.children)  # no child时显然也算同一族, 毕竟底层是father & child for loop
        ):
            return self.fold(node, simlified_child)
        return type(node).reconstruct(node, simlified_attr)

    def to_str(self, node: AstNode):
        """
        输入 AST，输出一个生成器，依次产出每一步化简的结果字符串。

        index 0 是原式，最后一个是最终结果。
        index n刚好是第n步化简的结果。
        """
        yield str(node)
        while not isinstance(node, NumberNode):
            node = self.simplify(node)
            yield str(node)

    def eval(self, node: AstNode):
        """
        求值器主函数，输入 AST，输出一个生成器，依次产出每一步的AstNode

        index 0 是原式，最后一个是最终结果。
        index n刚好是第n步化简的结果。
        """
        yield node
        while not isinstance(node, NumberNode):
            node = self.simplify(node)
            yield node


if __name__ == "__main__":  # pragma: no cover
    # 简单测试
    from .lexer import Lexer
    from .parser import Parser

    RNG = random.Random(42)  # 固定随机种子, 以便复现

    source = "2**2**2 % 2 + 5d(3d4 + 2)"
    tokens = Lexer.tokenize(source)
    print(f"Tokens: {Lexer.format_tokens(tokens)}")
    stmt = Parser(tokens).parse()
    if isinstance(stmt, ExprStmt):
        asttree = stmt.value
    else:
        raise TodoError("目前仅支持表达式语句的求值")
    print(f"AST: {asttree}")
    evaluator = Evaluator(rng=RNG)
    index = 0
    print("========== Evaluation Steps =========")
    for index, step in enumerate(evaluator.to_str(asttree)):
        print(f"Step {index}: {step}")
        if index >= 10:
            print("过多步骤, 可能进入死循环, 测试终止。")
            break
