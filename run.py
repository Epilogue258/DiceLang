import random
import sys

sys.path.insert(0, "src")

from DiceLang.interpreter import Interpreter
from DiceLang.result import ErrorRes, ExprRes, VarDefRes

RNG = random.Random(42)

tests = [
    # 表达式
    "1+2*3",
    "2^3^2",
    "3d6 + 5",
    # 变量
    "x = 5; x + 3",
    "hp = 15; hp = hp - 2; hp",
    "a, b = 10; a + b",
    # 复合赋值
    "x = 5; x += 3; x",
    "x = 10; x /= 3",
    "x = 2; x ^= 3",
    # 错误隔离
    "1+2; 5/0; 3*4",
    # 未定义
    "x += 5",
    "y = z + 1",
    # 非法字符
    "1 @ 2",
    # 空输入
    "",
]

if __name__ == "__main__":
    for text in tests:
        print(f"=== {text!r} ===")
        interp = Interpreter(text, rng=RNG)
        for r in interp():
            match r:
                case VarDefRes():
                    print(f"  {r}")
                case ExprRes():
                    for step in r:
                        print(f"  | {step}")
                    print(f"  => {r.value}")
                case ErrorRes():
                    print(f"  ERR: {r.value}")
        print()
