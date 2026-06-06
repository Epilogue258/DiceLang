from .astnode import AstNode
from .tokens import Token


class DiceLangError(Exception):
    """DiceLang 相关错误的基类。

    标准化属性（所有子类必须提供）：
    - pos: int | None     错误在源文本中的起始位置
    - length: int | None  错误片段长度（renderer 用 source[pos:pos+length] 切片标红）
    """
    pos: int | None
    length: int | None

    def __init__(self, message: str = "", **kwargs):
        super().__init__(message)
        self.pos = kwargs.pop("pos", None)
        self.length = kwargs.pop("length", None)
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

    def __init__(self, message, pos=None, length=None, **kwargs):
        super().__init__(message, pos=pos, length=length, **kwargs)


class ParserError(DiceLangError):
    """用于表示语法分析阶段的错误。"""

    def __init__(self, message: str = "", token: Token | None = None, pos=None, length=None, tokens=None, **kwargs):
        self.token = token
        self.pos = pos if pos is not None else (token.pos if token else None)
        self.length = length if length is not None else (len(token.text) if token else None)
        self.tokens = tokens
        super().__init__(message, pos=self.pos, length=self.length, token=token, tokens=tokens, **kwargs)


class EvaluatorError(DiceLangError):
    """用于表示计算/执行阶段的错误。"""

    def __init__(self, message: str = "", ast_tree: AstNode | None = None, **kwargs):
        self.ast_tree = ast_tree
        super().__init__(
            message,
            pos=ast_tree.pos if ast_tree else None,
            length=ast_tree.length if ast_tree else None,
            ast_tree=ast_tree,
            **kwargs,
        )


class TodoError(DiceLangError):
    def __init__(self, message: str = "", **kwargs):
        if not message:
            message = "这是条TODO错误, 理论上在上线时项目内不应有任何除此以外的引用。"
        super().__init__(message, **kwargs)
