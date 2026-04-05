# 学习用Pratt算法解决实际问题.
from enum import Enum, StrEnum
import re
import operator
import random
from typing import Any
from dataclasses import dataclass, field
from data import TokenType, Token, DiceResult, AstNode

class Lexer: # 词法分析器：输入字符串，输出 Token 流。
    def __init__(self, text: str):
        pass

class Parser: # 解析器：输入 Token 流，输出 AST（抽象语法树）。
    def __init__ (self, tokens: list[Token]):
        pass
    
class Evaluator: # 求值器：输入 AST，输出结果（包含中间过程）。
    def __init__(self, node: AstNode, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        pass


def eval_expr(expr: str) -> int:
    return 0

def main():
    random.seed(42) # 固定种子
    # 测试Lexer

    # 测试Parser

    # 测试Evaluator


    # 基本算术
    # assert eval_expr("3+5") == 8, "加法失败"
    # assert eval_expr("3*5") == 15, "乘法失败"
    # assert eval_expr("(2+3)*4") == 20, "括号失败"
    # assert eval_expr("2^3") == 8, "幂运算失败"
    # assert eval_expr("4+6*8^2**2") == 4 + 6 * (8**2**2), "多义幂运算失败"
    # assert eval_expr("10/2") == 5, "除法失败"
    # assert eval_expr("-2+5") == 3, "负数加法失败"
    assert eval_expr("3+-2") == 1, "负号减号二义性识别失败"
    # 随机测试
    # random_simple_test()
    # TODO: 骰子计算
    # 
    # TODO: 后缀运算
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