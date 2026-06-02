from dataclasses import dataclass
from typing import Any

from .error import DiceLangError


@dataclass(frozen=True, slots=True, kw_only=True)
class Result:
    value: Any

    def __str__(self):
        return str(self.value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExprRes(Result):
    value: int
    steps: tuple[str, ...]

    def __iter__(self):
        """迭代每一步的字符串表示。"""
        return iter(self.steps)

    def __str__(self):
        """调试用：逐行显示步骤。调用方如需自定义格式，直接 for step in result。"""
        return "\n".join(f"Step {i}: {s}" for i, s in enumerate(self.steps))


@dataclass(frozen=True, slots=True, kw_only=True)
class VarDefRes(Result):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroDefRes(Result):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorRes(Result):
    value: DiceLangError

    def __str__(self):
        return str(self.value)
