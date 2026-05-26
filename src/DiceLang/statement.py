from dataclasses import dataclass
from typing import Any

from .astnode import AstNode
from .error import DiceLangError, TodoError


@dataclass(frozen=True, slots=True, kw_only=True)
class Statement:
    value: Any


@dataclass(frozen=True, slots=True, kw_only=True)
class ExprStmt(Statement):
    value: AstNode


@dataclass(frozen=True, slots=True, kw_only=True)
class VarDefStmt(Statement):  # TODO
    value: list[tuple[str, AstNode, bool]]  # name, value, is_def_succeess
    # raise TodoError("VarDefStmt 尚未实现")


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroDefStmt(Statement):
    value: list[tuple[str, AstNode, bool]]  # name, value, is_def_succeess
    # raise TodoError("MacroDefStmt 尚未实现")


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorStmt(Statement):
    value: DiceLangError
