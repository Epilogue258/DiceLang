from dataclasses import dataclass
from tokens import TokenType

@dataclass(frozen=True)
class AstNode:
    pass

@dataclass(frozen=True)
class NumberNode(AstNode):
    value: int

@dataclass(frozen=True)
class DiceNode(AstNode):
    count: AstNode   # 左边的数字（可以是表达式）
    sides: AstNode   # 右边的数字（可以是表达式）

@dataclass(frozen=True)
class SelectorNode(AstNode):
    selector: TokenType  # HIGHEST/LOWEST/KEEP/THROW
    count: AstNode       # 选择数量
    
@dataclass(frozen=True)
class BinaryOpNode(AstNode):
    """
    二元运算符节点
    op: 运算符类型
    left: 左子表达式节点
    right: 右子表达式节点
    """
    op: TokenType # 为加减乘除等单独设计节点是不必要的——太繁琐
    left: AstNode
    right: AstNode
    selectors: list[SelectorNode]  # 有序的选择器链