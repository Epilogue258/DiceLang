from dataclasses import dataclass, field
from typing import Any
from enum import Enum, StrEnum

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
    # 函数调用相关
    WHITESPACE = "WHITESPACE" # 空格, 日后可能用于分割token,如区分12和1 2, 保留之, 但现阶段实际会被忽略
    COMMA = "COMMA" # "," e.g. reroll(d4, <, 3)
    IDENTIFIER = "IDENTIFIER" # 标识符, e.g. reroll...
    ASSIGN = "ASSIGN" # "=" e.g. x = 3d6, y = x + 2

    EOF = "EOF"

IDENTIFIER_TO_TYPE: dict[str, TokenType] = {
    'd': TokenType.DICE,
    'h': TokenType.HIGHEST,
    'l': TokenType.LOWEST,
    'k': TokenType.KEEP,
    't': TokenType.THROW,
}

SYMBOL_TO_TYPE: dict[str, TokenType] = {
    # 双字符运算符（注意顺序不重要，但消费时要按最长匹配）
    '**': TokenType.POW,
    '==': TokenType.EQ,
    '!=': TokenType.NEQ,
    '<=': TokenType.LTE,
    '>=': TokenType.GTE,
    # 单字符运算符
    '+': TokenType.PLUS,
    '-': TokenType.MINUS,
    '*': TokenType.MULTIPLY,
    '/': TokenType.DIVIDE,
    '%': TokenType.MOD,
    '^': TokenType.POW,
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '<': TokenType.LT,
    '>': TokenType.GT,
    '=': TokenType.ASSIGN,
}

STANDARD_SYMBOL: dict[str, str] = {
    "**": "^",
}

LONGEST_SYM_LENGTH = max(len(sym) for sym in SYMBOL_TO_TYPE.keys())

SYMBOLS = frozenset(''.join(SYMBOL_TO_TYPE.keys()))

def standardize_sym(symbol: str) -> str:
    return (STANDARD_SYMBOL.get(symbol, symbol))

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    text: str
    pos: int

@dataclass
class DiceResult: # TODO: 可能无需独立存在, 而隶属于EvalResult, 待定
    rolls: list[tuple[int, bool]] # [(1, is_chosen=T), (2, is_chosen=F), ...]

class AstNode:
    pass