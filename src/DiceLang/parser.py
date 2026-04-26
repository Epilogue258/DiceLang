from typing import Self

from astnode import (
    AstNode,
    BinaryOpNode,
    DiceNode,
    GroupNode,
    NumberNode,
    SelectorNode,
    UnaryOpNode,
)  # TODO 确保应导尽导
from error import ParserError, TodoError
from lexer import Lexer  # TODO 测试用，后期删除
from tokens import Token, TokenType


class Parser:  # TODO 解析器：输入 Token 流，输出 AST（抽象语法树）。
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

        if tokens and tokens[-1].type != TokenType.EOF:
            raise ParserError("Token流必须以EOF结尾", token=tokens[-1] if tokens else None)

        self.ast: AstNode = self.parse()

    @property
    def current(self) -> Token:
        # 总是返回当前指针指向的 Token
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
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

    def expect(self, *expected_type: TokenType, error: ParserError | None = None, offset=0) -> Self:  # 链式调用
        if self.peek(offset).type not in expected_type:
            raise (
                error
                if error
                else ParserError(
                    f"期望 {expected_type}, 得到类型为： {self.current.type} 位于 {self.current.pos}，内容为： {self.current.text}",
                    token=self.current,
                    pos=self.current.pos,
                )
            )
        return self

    def match(self, *expected_type: TokenType, offset=0) -> bool:
        return self.peek(offset).type in expected_type

    def get_prefix_bp(self, token: Token) -> int | None:
        return prefix_parselets.get(token.type)

    def get_infix_bp(self, token: Token) -> tuple[int, int] | None:
        return infix_parselets.get(token.type)

    def prefix_parse(self, token: Token) -> AstNode:
        match token.type:
            case TokenType.NUMBER:
                return NumberNode(token.value)
            case TokenType.PLUS | TokenType.MINUS:
                bp = self.get_prefix_bp(token)
                assert bp is not None  # 同类型检查器搏斗的产物，你可以自行去除看看为什么有这一行
                operand = self.parse(bp)
                return UnaryOpNode(token.type, operand)  # TODO fix
            case TokenType.IDENTIFIER:
                print(self.current)
                if self.match(TokenType.LPAREN):
                    # FuncCallNode Start
                    raise TodoError("FuncCallNode Start")
                else:
                    # VarNode Start
                    raise TodoError("VarNode")
            case TokenType.LPAREN:  # Return: GroupNode | FuncCallNode TODO: 验证函数调用是否可行
                group = []
                while not self.match(TokenType.RPAREN, TokenType.EOF):  # 说明解析后抵达的可能是「,」而非)
                    group.append(self.parse(0))
                self.expect(TokenType.RPAREN, error=ParserError("未找到右括号！", token=self.current, pos=self.current.pos)).consume()
                if not group:
                    raise ParserError("括号内不存在任何可被解析的值", tokens=self.tokens)
                if len(group) == 1:
                    return GroupNode(*group)
            case TokenType.EOF:
                raise TodoError("EOF")
            case _:
                raise ParserError(f"parse_prefix时得到类型为： {token.type} 位于 {token.pos}，内容为： {token.text}", token=self.current)

    def infix_parse(self, left: AstNode, op_token: Token, right_bp: int) -> AstNode:  # TODO right_bp很重要吗？
        match op_token.type:
            case TokenType.PLUS | TokenType.MINUS | TokenType.MULTIPLY | TokenType.DIVIDE | TokenType.POW | TokenType.MOD:
                right = self.parse(right_bp)
                return BinaryOpNode(op_token.type, left, right)
            case TokenType.DICE:
                right = self.parse(right_bp)
                return DiceNode(left, right, selectors=[])  # TODO selectors
            case _:  # TODO：日后可以添加用户自定义字典
                raise ParserError(f"不支持的中缀操作: {op_token.type}，位于{op_token.pos}, 内容: {op_token.text}")

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
            if infix_bp is None:  # EOF|RPAREN同样是None，故而无需特殊处理
                break

            left_bp, right_bp = infix_bp
            if left_bp < min_bp:
                break

            self.consume()  # 消耗中缀——在之前消耗的话会出现pos越界的情况，有点危险。

            left = self.infix_parse(left, op_token, right_bp)  # TODO：显然回传不一定是二元运算符
        return left

    def __str__(self):
        # 这其实没什么用，和Lexer做个语义对齐而已
        return f"<Parser: {self.ast}>" if self.ast else "<Parser: empty>"


# --- 优先级表 ---
prefix_parselets = {
    TokenType.PLUS: 10,  # 一元加
    TokenType.MINUS: 50,  # 一元减
    TokenType.DICE: 60,  # 缺省骰 d6 = 1d6
    # LPAREN 不需要绑定力，因为它是硬编码的特殊处理
}

infix_parselets: dict[TokenType, tuple[int, int]] = {
    TokenType.PLUS: (10, 11),
    TokenType.MINUS: (10, 11),
    TokenType.MULTIPLY: (20, 21),
    TokenType.DIVIDE: (20, 21),
    TokenType.MOD: (20, 21),
    TokenType.POW: (31, 30),  # 右结合幂运算 2^3^4 -> 2^(3^4)
    TokenType.DICE: (60, 61),  # 骰子是左结合的 2d6d8 -> (2d6)d8
}

if __name__ == "__main__":  # TODO 测试用
    sounce = "FUNC(1)"
    lexer = Lexer(sounce)

    print(f"\n{lexer!r}\n")
    parser = Parser(lexer.tokens)
    print(f"{parser}\n")
    print(f"{parser.ast}\n")

    # assert eval(sounce) == eval(str(parser.ast))
# 测试结果：
# 括号不对称出错：(()会提示括号不匹配，但是())则不会。
# (1+2)*（3*4）
# TODO 测试逗号
