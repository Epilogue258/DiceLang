import random

import pytest

from src.DiceLang.lexer import Lexer

RNG = random.Random(42)  # 固定随机种子, 以便复现


def test_fuzzing_parse():
    pass


# TODO
@pytest.mark.parametrize("tokens, expects", [(), ()])
def test_parse():
    pass
