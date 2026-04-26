from astnode import AstNode
from tokens import Token


class DiceLangError(Exception):
    """DiceLang 相关错误的基类。"""

    def __init__(self, message: str = ""):
        super().__init__(message)

    def _extra_info(self) -> dict[str, str]:
        return {}

    def __str__(self) -> str:
        msg = super().__str__() or self.__class__.__name__  # 短路
        info = self._extra_info()
        if not info:
            return msg
        details = "\n".join(f"  {k}: {v}" for k, v in info.items())
        return f"{msg}\n{details}"


class LexerError(DiceLangError):
    """用于表示词法分析阶段的错误。"""

    def __init__(self, message, text=None, pos=None):
        self.text = text
        self.pos = pos
        super().__init__(message)

    def _extra_info(self):
        info = {}
        if self.pos is not None:
            info["位置"] = str(self.pos)
        if self.text is not None:
            info["文本"] = repr(self.text)
        return info


class ParserError(DiceLangError):
    """用于表示语法分析阶段的错误。"""

    def __init__(self, message: str = "", token: Token | None = None, pos=None, tokens=None):
        self.token = token
        self.pos = pos
        self.tokens = tokens
        super().__init__(message)

    def _extra_info(self):
        info = {}
        if self.pos is not None:
            info["位置"] = str(self.pos)
        if self.token is not None:
            info["Token"] = repr(self.token)
        if self.tokens is not None:
            info["Token列表"] = repr(self.tokens)
        return info


class EvaluatorError(DiceLangError):
    """用于表示计算/执行阶段的错误。"""

    def __init__(self, message: str = "", ast_tree: AstNode | None = None):
        self.ast_tree = ast_tree
        super().__init__(message)

    def _extra_info(self):
        info = {}
        if self.ast_tree is not None:
            info["AST树"] = repr(self.ast_tree)  # TODO ASTnode层数过深？
        return info


class TodoError(DiceLangError):
    def __init__(self, message: str = ""):
        if not message:
            message = "这是条TODO错误，理论上在上线时项目内不应有任何除此以外的引用。"
        super().__init__(message)
