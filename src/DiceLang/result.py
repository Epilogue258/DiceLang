from dataclasses import dataclass
from typing import Any, NamedTuple

from .error import DiceLangError


class VarInfo(NamedTuple):
    """单个变量的赋值信息。"""

    name: str
    old: int | None  # None = 首次定义
    value: int  # 赋值后的新值


@dataclass(frozen=True, slots=True, kw_only=True)
class Result:
    value: Any = (
        None  # 子类按需重定义，有时需type: ignore[reportGeneralTypeIssues]，虽然kw_only已经保证了调用，主要是检查器会警告。
    )

    def __str__(self):
        return str(self.value) if self.value is not None else self.__class__.__name__


@dataclass(frozen=True, slots=True, kw_only=True)
class ExprRes(Result):
    value: int  # type: ignore[reportGeneralTypeIssues]
    steps: tuple[str, ...]

    def __iter__(self):
        """迭代每一步的字符串表示。"""
        return iter(self.steps)

    def __str__(self):
        """调试用：逐行显示步骤。调用方如需自定义格式，直接 for step in result。"""
        return "\n".join(f"Step {i}: {s}" for i, s in enumerate(self.steps))


@dataclass(frozen=True, slots=True, kw_only=True)
class VarDefRes(Result):
    vars: tuple[VarInfo, ...]

    def __str__(self):
        parts = []
        for v in self.vars:
            if v.old is None:
                parts.append(f"{v.name}: {v.value}")
            else:
                parts.append(f"{v.name}: {v.old} -> {v.value}")
        return "\n".join(parts)


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroDefRes(Result):
    names: tuple[str, ...]
    expr_str: str

    def __str__(self):
        names_str = ", ".join(self.names)
        return f"&{names_str}: {self.expr_str}"


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorRes(Result):
    value: DiceLangError  # type: ignore[reportGeneralTypeIssues]

    def __str__(self):
        return str(self.value)
