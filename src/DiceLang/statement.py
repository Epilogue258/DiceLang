from dataclasses import dataclass
from typing import Any

from .astnode import AstNode
from .error import DiceLangError, TodoError
from .tokens import TokenType


@dataclass(frozen=True, slots=True, kw_only=True)
class Statement:
    value: Any = None  # 子类按需重定义


@dataclass(frozen=True, slots=True, kw_only=True)
class ExprStmt(Statement):
    value: AstNode


@dataclass(frozen=True, slots=True, kw_only=True)
class VarDefStmt(Statement):
    names: tuple[str, ...]
    expr: AstNode
    op: TokenType = TokenType.ASSIGN


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroDefStmt(Statement):
    value: list[tuple[str, AstNode, bool]]  # name, value, is_def_succeess
    # raise TodoError("MacroDefStmt 尚未实现")


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorStmt(Statement):
    value: DiceLangError
