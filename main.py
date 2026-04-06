# 学习用Pratt算法解决实际问题.
from enum import Enum, StrEnum
import re
import operator
import random
from typing import Any, Callable
from dataclasses import dataclass, field
import data
from data import TokenType, Token, DiceResult, AstNode

def consume_while(predicate: Callable[[str], bool], text: str, pos: int, max_length: int | None = None) -> str:
    result = ""
    while pos < len(text) and predicate(text[pos]):
        result += text[pos]
        pos += 1
        if max_length is not None and len(result) >= max_length:
            break
    return result

class Lexer: # 词法分析器：输入字符串，输出 Token 流。
    def __init__(self, text: str):
        self.tokens = self.tokenize(text)
    
    def tokenize(self, text: str) -> list[Token]:
        index = 0
        tokens = []
        while index < len(text):
            ch = text[index]
            if ch.isspace():
                index += 1
                continue
            elif ch.isdigit():
                num = consume_while(str.isdigit, text, index)
                tokens.append(Token(TokenType.NUMBER, int(num), num, index))
                index += len(num)
            elif ch.isalpha():
                identifier = consume_while(str.isalpha, text, index)
                end_pos = index + len(identifier)
                if identifier.lower() in data.IDENTIFIER_TO_TYPE:
                    # 把dhkltr等lower, 标准化为1d6等, 这是为了同函数保持一致, 严格来说D这种大写其实更好
                    tokens.append(Token(data.IDENTIFIER_TO_TYPE[identifier.lower()], identifier.lower(), identifier, index))
                else: # 说不定是自定义变量, 而查询token是否存在并非Lexer的任务, 不然x = 5报错也太滑稽了
                    tokens.append(Token(TokenType.IDENTIFIER, identifier.lower(), identifier, index))
                index = end_pos
            elif ch in data.SYMBOLS:
                # 注意SYMBOLS和SYMBOL_TO_TYPE的区别, 前者是符号集合, 比如尽管不存在!这个token, 由于其为!=的一部分,in SYMBOLS为真
                symbol = consume_while(lambda c: c in data.SYMBOLS, text, index, max_length=data.LONGEST_SYM_LENGTH)
                # 然后, 对于1-(2), 会匹配成-(, 这时就需要回退到-
                while symbol not in data.SYMBOL_TO_TYPE and len(symbol) > 1:
                    symbol = symbol[:-1] # 对于上述例子, 这里回退后symbol变作-, (会在下次循环捕获, 如此实现最长匹配
                end_pos = index + len(symbol)
                if symbol in data.SYMBOL_TO_TYPE:
                    tokens.append(Token(data.SYMBOL_TO_TYPE[symbol], data.standardize_sym(symbol), symbol, index))
                else:
                    raise ValueError(f"未知的符号: {symbol} 位于索引{index}到{end_pos}部分")
                index = end_pos
            else:
                raise ValueError(f"未知的字符: {ch} 位于索引{index}部分")
        # while index < len(text): ends
        tokens.append(Token(TokenType.EOF, None, "", -1))
        return tokens

class Parser: # TODO 解析器：输入 Token 流，输出 AST（抽象语法树）。
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

        if tokens and tokens[-1].type != TokenType.EOF:
            raise ValueError("Token流必须以EOF结尾")
    
    @property
    def current(self) -> Token:
        # 总是返回当前指针指向的 Token
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, None, "", -1)

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, None, "", -1)

    def consume(self, expected_type: TokenType | None = None) -> Token:
        # 确认并移动指针
        token = self.current
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"期望 {expected_type}, 得到 {token.type} at {token.pos}")
        self.pos += 1
        return token
    
    def parse(self):
        prefix = self.consume()
        

    
class Evaluator: # 求值器：输入 AST，输出结果（包含中间过程）。
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        pass

    def eval(self, node: AstNode) -> DiceResult: # type hint在这里标红, 这不是错误, 只是因为之后再实现这里的pass
        pass


def eval_expr(expr: str) -> int:
    return 0

def main():
    random.seed(42) # 固定种子
    lexer = Lexer("1D6 if == 1 : 2")
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
    # assert eval_expr("3+-2") == 1, "负号减号二义性识别失败"
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
Parser：实现 Pratt 解析，先只处理算术和括号。测试用例：手工构造 token 列表 → 期望 AST。

Evaluator：实现算术求值，返回 EvalResult。测试用例：手工构造 AST → 期望数值和步骤字符串。

集成：在 eval_expr 中串联三者，测试 "2+3" 等。

加入骰子：扩展 Lexer 识别 d；Parser 中 d 作为中缀运算符；Evaluator 中实现 Dice 节点求值（带随机数，用依赖注入 rng）。测试用范围测试 + 固定种子。

加入后缀筛选：修改 Dice 节点带后缀列表，Evaluator 实现管道。测试用 Mock 方法。
"""

# TODO
# | 方法              | 作用                                                                                                                       |
# | `.next()`       | 消费当前 token，并前进到下一个。                                                                                           |
# | `.junk()`       | 跳过当前 token（或连续跳过多个无效 token），直到找到某个“同步点”（比如遇到分号、右括号、运算符等）。具体行为由实现定义。 |
# | `.expect(kind)` | 断言下一个 token 是某种类型，如果不是则报告错误，并尝试恢复（比如调用 `.junk()`跳过）。                                  |