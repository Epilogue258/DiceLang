from dataclasses import dataclass
from typing import Any

from .error import DiceLangError


@dataclass(frozen=True, slots=True, kw_only=True)
class Result:
    value: Any = None  # 子类按需重定义

    def __str__(self):
        return str(self.value) if self.value is not None else self.__class__.__name__


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
    names: tuple[str, ...]
    old_values: dict[str, int | None]  # None = 首次定义
    new_value: int

    def __str__(self):
        parts = []
        for name in self.names:
            old = self.old_values[name]
            if old is None:
                parts.append(f"{name}: {self.new_value}")
            else:
                parts.append(f"{name}: {old} -> {self.new_value}")
        return "\n".join(parts)


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroDefRes(Result):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorRes(Result):
    value: DiceLangError

    def __str__(self):
        return str(self.value)
