"""
DiceLang AST 节点定义。
为什么使用 `frozen=True, slots=True`：
- `frozen=True`：AST 节点在构造完成后不可变，避免解析/求值阶段被意外修改。
- `slots=True`：减少节点对象内存开销，适合大量小对象的场景。

设计约束：
- 所有节点使用 `frozen=True, slots=True`：降低内存占用，并防止解析/求值阶段误修改。
- 解析器按自底向上构建语法树。

说明：
- 重写了Str用以方便查看输出，如不需要结构化，请调用__repr__()。dataclass会自动递归调用内层元素的__repr__()
- `DiceNode.selectors` 必须保持源码顺序，因为后缀修饰器语义依赖顺序。
"""

from dataclasses import dataclass

from tokens import TokenType


@dataclass(frozen=True, slots=True)
class AstNode:
    def __str__(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True, slots=True)
class NumberNode(AstNode):
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class SelectorNode(AstNode):
    selector: TokenType  # HIGHEST/LOWEST/KEEP/THROW
    count: AstNode  # 选择数量


@dataclass(frozen=True, slots=True)
class DiceNode(AstNode):
    count: AstNode  # 左边的数字（可以是表达式）
    sides: AstNode  # 右边的数字（可以是表达式）
    selectors: list[SelectorNode]  # 有序的选择器链

    def __str__(self) -> str:  # TODO 输出时处理selectors
        return f"({self.count} D {self.sides})"


@dataclass(frozen=True, slots=True)
class BinaryOpNode(AstNode):
    """
    二元运算符节点
    op: 运算符类型
    left: 左子表达式节点
    right: 右子表达式节点
    """

    op: TokenType  # 为加减乘除等单独设计节点是不必要的——太繁琐
    left: AstNode
    right: AstNode

    def __str__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


@dataclass(frozen=True, slots=True)
class UnaryOpNode(AstNode):
    """
    一元运算符节点
    op: 运算符类型
    operand: 操作数节点
    """

    op: TokenType
    operand: AstNode

    def __str__(self) -> str:
        return f"({self.op}{self.operand})"


@dataclass(frozen=True, slots=True)
class GroupNode(AstNode):
    group: AstNode

    def __str__(self) -> str:
        # return f"{{:{', '.join(map(str, self.group))}:}}"  # 之所以采用{: xxx :}形式是为了同print时自动生成的括弧作出区分
        return f"( {self.group} )"


@dataclass(frozen=True, slots=True)
class FuncCallNode(AstNode):
    groups: list[AstNode]

    def __str__(self) -> str:
        # return f"{{:{', '.join(map(str, self.group))}:}}"  # TODO: 之所以采用{: xxx :}形式是为了同print时自动生成的括弧作出区分
        return f"( {', '.join(map(str, self.groups))} )"


@dataclass
class DiceResult:  # TODO: 可能无需独立存在, 而隶属于EvalResult, 待定
    rolls: list[tuple[int, bool]]  # [(1, is_chosen=T), (2, is_chosen=F), ...]


if __name__ == "__main__":
    num1 = UnaryOpNode(TokenType.MINUS, NumberNode(11))
    num2 = NumberNode(22)
    plus = BinaryOpNode(TokenType.PLUS, num1, num2)
    print(f"{plus}\n")
    print(f"{plus!r}\n")
