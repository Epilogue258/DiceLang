import random

import pytest

from src.DiceLang.error import TodoError
from src.DiceLang.lexer import Lexer

RNG = random.Random(42)  # 固定随机种子, 以便复现


def test_fuzzing_parse():
    raise TodoError("test_fuzzing_parse")


# TODO
@pytest.mark.parametrize("tokens, expects", [(), ()])
def test_parse():
    raise TodoError("test_parse")
