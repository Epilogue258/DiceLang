"""
DiceLang AST 节点定义。
为什么使用 `frozen=True, slots=True`：
- `frozen=True`：AST 节点在构造完成后不可变，避免解析/求值阶段被意外修改。
- `slots=True`：减少节点对象内存开销，适合大量小对象的场景。

设计约束：
- 所有节点使用 `frozen=True, slots=True`：降低内存占用，并防止解析/求值阶段误修改。
- 解析器按自底向上构建语法树。

说明：
- `DiceNode.selectors` 必须保持源码顺序，因为后缀修饰器语义依赖顺序。
"""

from __future__ import (
    annotations,
)  # 延迟求值, 这是为了降低children返回Self时可能的误导, 因为显然其子节点虽然仍然是节点, 但不一定是调用方相同的节点Self

import enum
from dataclasses import dataclass, fields
from typing import NamedTuple, cast

from .tokens import TokenType


class Roll(NamedTuple):
    """骰子结果中单颗骰子的状态。

    value    — 骰值
    sides    — 源骰子面数（D6/D8/...）
    marked   — 是否被 h/l/if 等选择器标记
    exploded — 是否来自爆炸（追加骰）
    """

    value: int
    sides: int
    marked: bool = False
    exploded: bool = False


class Family(enum.Flag):  # 底层就是位掩码啦
    NONE = 0
    ADD = enum.auto()
    MUL = enum.auto()
    POW = enum.auto()
    DICE = enum.auto()
    SELECTOR = enum.auto()
    ALL = ADD | MUL | POW | DICE | SELECTOR


# 我也不想用kw_only, 但是不加的话就会出现dataclass的坑:
# 其默认重载了init, 但是又要求参数按照无默认值在前有默认值在后的顺序传入, 这就导致了基类的默认值在子类再次出现后会导致参数位置混乱
# 虽然目前没有这个问题, 但是在一次中间迭代中出现了这个现象, 导致了非常恼人的错误, 尽管后来发现这个迭代事实上是不必要的, 但仍然保留了kw_only
# 多说无益, 强制所有参数必须以关键字传入就完全避免了这个问题, 如果不理解自己试试不这么做会如何吧
@dataclass(frozen=True, slots=True, kw_only=True)
class AstNode:
    pos: int | None = None
    length: int | None = None

    def __str__(self) -> str:
        """子类重载为用于人类可读的简洁输出；如需结构化表示，请使用 repr。"""
        return self.__class__.__name__

    def __iter__(self):
        # 获取所有数据类的值
        for field in fields(self):
            yield getattr(self, field.name)

    @property
    def children(self) -> list[AstNode]:
        """返回所有子节点，供求值器使用。"""
        return [child for child in self if isinstance(child, AstNode)]

    @property
    def family(self) -> Family:
        return Family.NONE

    @staticmethod
    def reconstruct(node: AstNode, attrs: list) -> AstNode:
        """用属性列表重建同类型节点（兼容 kw_only）"""
        field_names = [f.name for f in fields(node)]
        return type(node)(**dict(zip(field_names, attrs, strict=True)))


@dataclass(frozen=True, slots=True, kw_only=True)
class NumberNode(AstNode):
    value: int

    def __str__(self) -> str:
        return str(self.value)

    @property
    def family(self) -> Family:  # TODO
        return Family.ALL


@dataclass(frozen=True, slots=True, kw_only=True)
class ModifierNode(AstNode):
    """骰子后缀修饰器基类"""


@dataclass(frozen=True, slots=True, kw_only=True)
class HighestMod(ModifierNode):
    """hN：标记最高的 N 个"""

    count: AstNode

    def __str__(self) -> str:
        return f"h{self.count}"


@dataclass(frozen=True, slots=True, kw_only=True)
class LowestMod(ModifierNode):
    """lN：标记最低的 N 个"""

    count: AstNode

    def __str__(self) -> str:
        return f"l{self.count}"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConditionMod(ModifierNode):
    """if cond N：标记满足条件的元素"""

    condition: TokenType
    threshold: AstNode

    def __str__(self) -> str:
        return f"if {self.condition} {self.threshold}"


@dataclass(frozen=True, slots=True, kw_only=True)
class KeepMod(ModifierNode):
    """k：保留标记元素，清除标记"""

    def __str__(self) -> str:
        return "k"


@dataclass(frozen=True, slots=True, kw_only=True)
class ThrowMod(ModifierNode):
    """t：丢弃标记元素，清除标记"""

    def __str__(self) -> str:
        return "t"


@dataclass(frozen=True, slots=True, kw_only=True)
class CountMod(ModifierNode):
    """count / ifc：统计标记元素个数（而非求和）"""

    is_ifc: bool = False

    def __str__(self) -> str:
        return "ifc" if self.is_ifc else "count"


@dataclass(frozen=True, slots=True, kw_only=True)
class MapMod(ModifierNode):
    """:N 将当前所有被标记元素的值替换为 N，并清除标记。"""

    map_to: AstNode

    def __str__(self) -> str:
        return f": {self.map_to}"


@dataclass(frozen=True, slots=True, kw_only=True)
class DiceNode(AstNode):
    count: AstNode
    sides: AstNode
    selectors: list[ModifierNode]  # 有序的选择器链

    @property
    def family(self) -> Family:
        return Family.DICE

    def __str__(self) -> str:  # TODO 输出时处理selectors
        return f"{self.count}D{self.sides}"


@dataclass(frozen=True, slots=True, kw_only=True)
class DiceResNode(AstNode):
    rolls: tuple[Roll, ...]
    selectors: tuple[ModifierNode, ...]

    @property
    def family(self) -> Family:
        if self.selectors:
            return Family.DICE
        return Family.ALL

    def sum(self) -> int:
        """有标记求和标记项，无标记全求。"""
        marked = [r.value for r in self.rolls if r.marked]
        return sum(marked or [r.value for r in self.rolls])

    def __str__(self) -> str:
        def fmt(r: Roll) -> str:
            inner = f"D{r.sides}!{r.value}" if r.exploded else str(r.value)
            return f"({inner})" if r.marked else inner

        return f"[{', '.join(fmt(r) for r in self.rolls)}]"


@dataclass(frozen=True, slots=True, kw_only=True)
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

    @property
    def family(self) -> Family:
        match self.op:
            case TokenType.PLUS | TokenType.MINUS:
                return Family.ADD
            case TokenType.MULTIPLY | TokenType.DIVIDE | TokenType.MOD:
                return Family.MUL
            case TokenType.POW:
                return Family.POW
            case _:  # pragma: no cover
                return Family.NONE  # 正常来说这不应该被触发, 是不是漏了运算符啦?

    def __str__(self) -> str:
        return f"{self.left} {self.op} {self.right}"


@dataclass(frozen=True, slots=True, kw_only=True)
class UnaryOpNode(AstNode):
    """
    一元运算符节点
    op: 运算符类型
    operand: 操作数节点
    """

    op: TokenType
    operand: AstNode

    @property
    def family(self) -> Family:
        return Family.ALL

    def __str__(self) -> str:
        return f"{self.op}{self.operand}"


# frozen会自动生成hash, 不过放宽心, 会自动报错的啦: TypeError: unhashable type: 'list'
@dataclass(frozen=True, slots=True, kw_only=True, unsafe_hash=False)
class GroupNode(AstNode):
    group: list[AstNode]
    selectors: tuple[ModifierNode, ...] = ()

    def __iter__(self):
        yield from self.group

    @property
    def family(self) -> Family:
        if self.selectors:
            return Family.SELECTOR  # 带选择器时不参与同类折叠，由 fold 显式处理
        res = Family.ALL
        for atom in self.group:
            res &= atom.family
        return res if res == Family.ALL else Family.NONE

    @staticmethod
    def reconstruct(node: AstNode, attrs: list) -> GroupNode:
        node = cast(GroupNode, node)
        return GroupNode(group=attrs, selectors=node.selectors, pos=node.pos, length=node.length)

    def __str__(self) -> str:
        inner = f"({', '.join(map(str, self.group))})"
        if self.selectors:
            inner += "".join(str(s) for s in self.selectors)
        return inner


@dataclass(frozen=True, slots=True, kw_only=True)
class VarNode(AstNode):
    name: str

    @property
    def family(self) -> Family:
        return Family.NONE  # 与任何节点不同族, 故而至少需要化简一次

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroRefNode(AstNode):
    name: str

    @property
    def family(self) -> Family:
        return Family.NONE

    def __str__(self) -> str:
        return f"&{self.name}"


@dataclass(frozen=True, slots=True, kw_only=True)
class FuncCallNode(AstNode):  # TODO FUNCALL
    func: str
    args: GroupNode

    def __iter__(self):
        yield from self.args

    @property
    def family(self) -> Family:
        res = Family.ALL
        for atom in self.args:
            res &= atom.family
        return res if res == Family.ALL else Family.NONE

    @staticmethod
    def reconstruct(node: AstNode, attrs: list) -> AstNode:
        return FuncCallNode(func=node.func, args=GroupNode(group=attrs))

    def __str__(self) -> str:
        return f"{self.func}{self.args}"
