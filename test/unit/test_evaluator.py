import random
from typing import Any

import pytest

from src.DiceLang.error import TodoError
from src.DiceLang.lexer import Lexer
from src.DiceLang.tokens import (
    Token,
)

RNG = random.Random(42)  # 固定随机种子, 以便复现


def test_fuzzing_eval():
    raise TodoError("test_fuzzing_eval")


def test_eval():
    raise TodoError("test_eval")
