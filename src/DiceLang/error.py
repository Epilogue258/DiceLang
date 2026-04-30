from .astnode import AstNode
from .tokens import Token


class DiceLangError(Exception):
    """DiceLang 相关错误的基类。"""

    def __init__(self, message: str = "", **kwargs):
        super().__init__(message)
        self._extra: dict[str, object] = kwargs

    def _extra_info(self) -> dict[str, str]:
        return {k: repr(v) for k, v in self._extra.items() if v is not None}

    def __str__(self) -> str:
        msg = super().__str__() or self.__class__.__name__
        info = self._extra_info()
        if not info:
            return msg
        details = "\n".join(f"  {k}: {v}" for k, v in info.items())
        return f"{msg}\n{details}"


class LexerError(DiceLangError):
    """用于表示词法分析阶段的错误。"""

    def __init__(self, message, text=None, pos=None, **kwargs):
        self.text = text
        self.pos = pos
        super().__init__(message, text=text, pos=pos, **kwargs)


class ParserError(DiceLangError):
    """用于表示语法分析阶段的错误。"""

    def __init__(self, message: str = "", token: Token | None = None, pos=None, tokens=None, **kwargs):
        self.token = token
        self.pos = pos
        self.tokens = tokens
        super().__init__(message, token=token, pos=pos, tokens=tokens, **kwargs)


class EvaluatorError(DiceLangError):
    """用于表示计算/执行阶段的错误。"""

    def __init__(self, message: str = "", ast_tree: AstNode | None = None, **kwargs):
        self.ast_tree = ast_tree
        super().__init__(message, ast_tree=ast_tree, **kwargs)


class TodoError(DiceLangError):
    def __init__(self, message: str = "", **kwargs):
        if not message:
            message = "这是条TODO错误，理论上在上线时项目内不应有任何除此以外的引用。"
        super().__init__(message, **kwargs)
