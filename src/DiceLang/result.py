from dataclasses import dataclass
from typing import Any

from .error import DiceLangError


@dataclass(frozen=True, slots=True, kw_only=True)
class Result:
    value: Any


@dataclass(frozen=True, slots=True, kw_only=True)
class ExprRes(Result):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class VarDefRes(Result):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroDefRes(Result):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorRes(Result):
    value: DiceLangError
