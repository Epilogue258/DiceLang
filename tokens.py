"""
DiceLang 的词法单元（Token）与词法类型定义。

本模块职责：
- 定义 `TokenType`：词法分析阶段输出的离散类型集合。
- 定义 `Token`：不可变、轻量的词法单元对象。
- 提供基础优先级表（供解析器参考）。

设计约定：
- `Token` 使用 `@dataclass(frozen=True, slots=True)`：
  - `frozen=True`：防止词法结果在后续阶段被意外篡改；
  - `slots=True`：减少大量 Token 对象的内存开销。
- `Token.value` 保存“语义值”（如 NUMBER 的 int 值），`Token.text` 保留原始文本片段。
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TokenType(StrEnum):
    """
    词法分析器输出的Token类型.
    """

    # 基础运算
    DICE = "DICE"  # D/d, e.g. 3d6, 2D10
    NUMBER = "NUMBER"  # 1, 2, 3, ...
    PLUS = "PLUS"  # +
    MINUS = "MINUS"  # -
    MULTIPLY = "MULTIPLY"  # *
    DIVIDE = "DIVIDE"  # /, 由于跑团需要, 这为地板除法, 如7/2=3
    MOD = "MOD"  # %
    POW = "POW"  # 1 ^ 2, or 3d6 ** 5, ^同**通用
    LPAREN = "LPAREN"  # (
    RPAREN = "RPAREN"  # )
    # 比较运算
    LT = "LT"  # <, 3d6 < (5 < 6)
    GT = "GT"  # >, 3d6 > (5 > 6)
    EQ = "EQ"  # ==, 3d6 == 5
    LTE = "LTE"  # <=, 3d6 <= (5 <= 6)
    GTE = "GTE"  # >=, 3d6 >= (5 >= 6)
    NEQ = "NEQ"  # !=, 3d6 != (5 != 6)
    # 后缀筛选, 这类运算符区分选择与删除, 是为了便于嵌套处理, 如h3kl1意为在最大的三个中取最小(第三名)
    HIGHEST = "HIGHEST"  # h, e.g. 4d6h3 = 4d6选中最大的三个骰子
    LOWEST = "LOWEST"  # l, e.g. 4d6l2 = 4d6选中最小的两个骰子
    KEEP = "KEEP"  # k, e.g. 4d6h3k = 4d6选中最大的三个骰子并保存, 弃置剩余结果, 清除选中
    THROW = "THROW"  # t, e.g. 4d6h3t = 4d6选中最大的三个骰子并丢弃, 保存选中结果, 清除选中
    EXPLODE = "EXPLODE"  # 爆炸骰，如：1D6!、2D4e
    # 函数调用相关
    IF = "IF"
    IFCOUNT = "IFCOUNT"  # if c 的语法糖
    COUNT = "COUNT"
    MAX = "max"
    MIN = "min"
    WHITESPACE = "WHITESPACE"  # 空格, 日后可能用于分割token,如区分12和1 2, 保留之, 但现阶段实际会被忽略
    COMMA = "COMMA"  # "," e.g. reroll(d4, <, 3)
    COLON = "COLON"  # 负责转换，如：1D8 if ==1 : 2
    IDENTIFIER = "IDENTIFIER"  # 标识符, e.g. reroll...
    ASSIGN = "ASSIGN"  # "=" e.g. x = 3d6, y = x + 2

    EOF = "EOF"

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"  # 不显示 pos 和 text


@dataclass(frozen=True, slots=True)
class Token:
    """
    词法单元对象。
    字段：
    - type: Token 类型（TokenType）
    - value: 语义值（如数字、标识符文本等）
    - text: 源码中的原始片段
    - pos: 在输入串中的起始位置（用于报错定位）
    """

    type: TokenType
    value: Any
    text: str
    pos: int


@dataclass
class DiceResult:  # TODO: 可能无需独立存在, 而隶属于EvalResult, 待定
    rolls: list[tuple[int, bool]]  # [(1, is_chosen=T), (2, is_chosen=F), ...]
