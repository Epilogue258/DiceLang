# 学习用Pratt算法解决实际问题.
from enum import Enum, StrEnum
import re
import operator
import random
from typing import Any
from dataclasses import dataclass, field

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

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    text: str
    pos: int

@dataclass
class DiceResult:
    rolls: list[tuple[int, bool]] # [(1, is_chosen=T), (2, is_chosen=F), ...]

class Lexer: # 词法分析器：输入字符串，输出 Token 流。
    def __init__(self, text: str, rng: random.Random | None = None):
        pass

class Parser: # TODO
    def __init__ (self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.lbp_table: dict[TokenType, int] = {...}
        self.rbp_table: dict[TokenType, int] = {...}
    
class Evaluator: # TODO
    def __init__(self, text: str, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        pass


def eval_expr(expr: str) -> int:
    return 0

def main():
    random.seed(42) # 固定种子
    # 基本算术
    assert eval_expr("3+5") == 8, "加法失败"
    assert eval_expr("3*5") == 15, "乘法失败"
    assert eval_expr("(2+3)*4") == 20, "括号失败"
    assert eval_expr("2^3") == 8, "幂运算失败"
    assert eval_expr("4+6*8^2**2") == 4 + 6 * (8**2**2), "多义幂运算失败"
    assert eval_expr("10/2") == 5, "除法失败"
    assert eval_expr("-2+5") == 3, "负数加法失败"
    assert eval_expr("3+-2") == 1, "负号减号二义性识别失败"
    # 骰子计算
    # todo
    # 后缀运算
    # todo
    print("所有测试通过！")

if __name__ == "__main__":
    main()

# TODO:
"""
完成以下实现
1. Lexer（词法分析器）：输入字符串，输出 Token 流。
2. Parser（解析器）：输入 Token 流，输出 AST（抽象语法树）。
3. Evaluator（求值器）：输入 AST，输出结果（包含中间过程）。
了解如何解决骰子表达式的测试, 带随机性就有点麻烦了.
"""