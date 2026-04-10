from dataclasses import dataclass
from typing import Any
from enum import StrEnum

class TokenType(StrEnum):
    """
    词法分析器输出的Token类型.
    """
    # 基础运算
    DICE = "DICE" # D/d, e.g. 3d6, 2D10
    NUMBER = "NUMBER" # 1, 2, 3, ...
    PLUS = "PLUS" # +
    MINUS = "MINUS" # -
    MULTIPLY = "MULTIPLY" # *
    DIVIDE = "DIVIDE" # /, 由于跑团需要, 这为地板除法, 如7/2=3
    MOD = "MOD" # %
    POW = "POW" # 1 ^ 2, or 3d6 ** 5, ^同**通用
    LPAREN = "LPAREN" # (
    RPAREN = "RPAREN" # )
    # 比较运算
    LT = "LT" # <, 3d6 < (5 < 6)
    GT = "GT" # >, 3d6 > (5 > 6)
    EQ = "EQ" # ==, 3d6 == 5
    LTE = "LTE" # <=, 3d6 <= (5 <= 6)
    GTE = "GTE" # >=, 3d6 >= (5 >= 6)
    NEQ = "NEQ" # !=, 3d6 != (5 != 6)
    # 后缀筛选, 这类运算符区分选择与删除, 是为了便于嵌套处理, 如h3kl1意为在最大的三个中取最小(第三名)
    HIGHEST = "HIGHEST" # h, e.g. 4d6h3 = 4d6选中最大的三个骰子
    LOWEST = "LOWEST" # l, e.g. 4d6l2 = 4d6选中最小的两个骰子
    KEEP = "KEEP" # k, e.g. 4d6h3k = 4d6选中最大的三个骰子并保存, 弃置剩余结果, 清除选中
    THROW = "THROW" # t, e.g. 4d6h3t = 4d6选中最大的三个骰子并丢弃, 保存选中结果, 清除选中
    EXPLODE = "EXPLODE" # 爆炸骰，如：1D6!、2D4e
    # 函数调用相关
    IF = "IF"
    IFCOUNT = "IFCOUNT" # if c 的语法糖
    COUNT = "COUNT"
    MAX = "max"
    MIN = "min"
    WHITESPACE = "WHITESPACE" # 空格, 日后可能用于分割token,如区分12和1 2, 保留之, 但现阶段实际会被忽略
    COMMA = "COMMA" # "," e.g. reroll(d4, <, 3)
    COLON = "COLON" # 负责转换，如：1D8 if ==1 : 2
    IDENTIFIER = "IDENTIFIER" # 标识符, e.g. reroll...
    ASSIGN = "ASSIGN" # "=" e.g. x = 3d6, y = x + 2

    EOF = "EOF"

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"   # 不显示 pos 和 text

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    text: str
    pos: int

@dataclass
class DiceResult: # TODO: 可能无需独立存在, 而隶属于EvalResult, 待定
    rolls: list[tuple[int, bool]] # [(1, is_chosen=T), (2, is_chosen=F), ...]

precedence = { # TODO: 仍然需要补充不少优先级
    # 基础运算
    TokenType.PLUS: 10,
    TokenType.MINUS: 10,
    TokenType.MULTIPLY: 20,
    TokenType.DIVIDE: 20,
    TokenType.MOD: 20,
    TokenType.POW: 30,
    
    # 骰子专用（优先级通常比乘法高？或者特殊处理？）
    TokenType.DICE: 60, 
    
    # 后缀修饰符（优先级最高，因为要紧紧绑定左边的骰子）
    TokenType.EXPLODE: 40,
    TokenType.IF: 40,    # if 也是后缀修饰符
    TokenType.COUNT: 50, # c 优先级更高
}

prefix_parselets = None # TODO prefix_parselets