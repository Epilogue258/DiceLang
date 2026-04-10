# 学习用Pratt算法解决实际问题.
import random
# tag


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