import pytest
import main
from main import Token, TokenType, AstNode, DiceResult
import random

RNG = random.Random(42) # 固定随机种子, 以便复现

# fuzzing test
def test_fuzzing_lex():
    pass

def test_fuzzing_parse():
    pass

def test_fuzzing_eval():
    pass

# 固定case的测试
def test_lex():
    pass

def test_parse():
    pass

def test_eval():
    pass

if __name__ == "__main__":
    pytest.main()