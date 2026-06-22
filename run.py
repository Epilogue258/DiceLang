import random
import sys
import time

sys.path.insert(0, "src")

from DiceLang.interpreter import Interpreter
from DiceLang.result import ErrorRes, ExprRes, MacroDefRes, VarDefRes

RNG = random.Random(42)

tests = [
    # 表达式
    "x=1; &y=1d6;3 * &y",
    "1+2*2",
    "3d6 e(3d6d8d10)",
    "3d6 re (3d6d8d10)",
]

if __name__ == "__main__":
    N = 200
    for text in tests:
        # 计时
        start = time.perf_counter()
        for _ in range(N):
            interp = Interpreter(text, rng=random.Random(42))
            list(interp())
        us = (time.perf_counter() - start) / N * 1_000_000

        # 单次输出
        print(f"=== {text!r} ===")
        interp = Interpreter(text, rng=RNG)
        for r in interp():
            match r:
                case VarDefRes() | MacroDefRes():
                    print(f"  {r}")
                case ExprRes():
                    for step in r:
                        print(f"  | {step}")
                    print(f"  => {r.value}")
                case ErrorRes():
                    print(f"  ERR: {r.value}")
        print(f"  time: {us:.1f} μs\n")
