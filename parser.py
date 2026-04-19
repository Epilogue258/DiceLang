from time import sleep
from typing import Self

from astnode import (
    AstNode,
    BinaryOpNode,
    DiceNode,
    NumberNode,
    SelectorNode,
    UnaryOpNode,
)  # TODO 确保应导尽导
from tokens import Token, TokenType


class Parser:  # TODO 解析器：输入 Token 流，输出 AST（抽象语法树）。
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

        if tokens and tokens[-1].type != TokenType.EOF:
            raise ValueError("Token流必须以EOF结尾")

    @property
    def current(self) -> Token:
        # 总是返回当前指针指向的 Token
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:  # TODO：peek：可能实际并不需要，待定
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, None, "", -1)

    def consume(self) -> Token:
        """消耗掉一个索引，没有做越界检查，所以注意返回判断EOF的情况。

        Returns:
            Token: 返回被消费掉的Token
        """
        current = self.current
        self.pos += 1
        return current

    def expect(self, expected_type: TokenType) -> Self:  # 链式调用试试？
        if self.current.type != expected_type:
            raise SyntaxError(
                f"期望 {expected_type}, 得到类型为： {self.current.type} 位于 {self.current.pos}，内容为： {self.current.text}"
            )
        return self

    def match(self, expected_type: TokenType) -> bool:
        return self.current.type == expected_type

    def get_prefix_bp(self, token: Token) -> int | None:
        return prefix_parselets.get(token.type)

    def get_infix_bp(self, token: Token) -> tuple[int, int] | None:
        return infix_parselets.get(token.type)

    def prefix_parse(self, token: Token) -> AstNode:
        match token.type:
            case TokenType.NUMBER:
                return NumberNode(token.value)
            case TokenType.PLUS | TokenType.MINUS:  # TODO: +1 or -1 的前缀处理
                return UnaryOpNode(token.type, self.prefix_parse(self.consume()))
            case _:
                raise SyntaxError(f"parse_prefix时得到类型为： {token.type} 位于 {token.pos}，内容为： {token.text}")

    def infix_parse(self, left: AstNode, op_token: Token, right_bp: int) -> AstNode:
        match op_token.type:
            case TokenType.PLUS | TokenType.MINUS | TokenType.MULTIPLY | TokenType.DIVIDE | TokenType.POW:
                right = self.parse(right_bp)  # 这个递归关系有点复杂，要慢慢捋清楚
                return BinaryOpNode(op_token.type, left, right)
            case _:  # TODO：日后可以添加用户自定义字典
                raise SyntaxError(f"不支持的中缀操作: {op_token.type}，位于{op_token.pos}, 内容: {op_token.text}")

    def parse(self, min_bp: int = 0) -> AstNode:  # TODO 测试空输入
        """根据上一个绑定力返回最终的树

        Args:
            min_bp (int, optional): _description_. Defaults to 0.

        Returns:
            AstNode: 返回一棵AST树，其中绑定力更高的OP总是位于树顶
        """
        left = self.prefix_parse(self.consume())  # 消耗前缀

        # 中缀解析
        while True:
            op_token = self.current  # 查看中缀
            infix_bp = self.get_infix_bp(op_token)
            if infix_bp is None:  # EOF同样是None，故而无需对EOF特殊处理
                break

            left_bp, right_bp = infix_bp
            if left_bp < min_bp:
                break

            self.consume()  # 消耗中缀——在之前消耗的话会出现pos越界的情况，有点危险。

            left = self.infix_parse(left, op_token, right_bp)  # TODO：显然回传不一定是二元运算符
        return left


# --- 优先级表 ---
prefix_parselets = {
    TokenType.PLUS: 10,  # 一元加
    TokenType.MINUS: 10,  # 一元减
    TokenType.DICE: 60,  # 缺省骰 d6 = 1d6
    # LPAREN 不需要绑定力，因为它是硬编码的特殊处理
}

infix_parselets: dict[TokenType, tuple[int, int]] = {
    TokenType.PLUS: (10, 11),
    TokenType.MINUS: (10, 11),
    TokenType.MULTIPLY: (20, 21),
    TokenType.DIVIDE: (20, 21),
    TokenType.MOD: (20, 21),
    TokenType.DICE: (40, 41),  # 骰子是左结合的 2d6d8 -> (2d6)d8
    TokenType.POW: (31, 30),  # 右结合幂运算 2^3^4 -> 2^(3^4)
}
