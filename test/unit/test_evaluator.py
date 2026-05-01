import random
from typing import Any

import pytest

from DiceLang.error import LexerError, TodoError
from DiceLang.lexer import Lexer
from DiceLang.tokens import (
    Token,
)

RNG = random.Random(42)  # 固定随机种子, 以便复现


@pytest.mark.xfail(reason="待实现", strict=True)
def test_fuzzing_eval():
    raise TodoError("test_fuzzing_eval")


@pytest.mark.xfail(reason="待实现", strict=True)
def test_eval():
    raise TodoError("test_eval")
