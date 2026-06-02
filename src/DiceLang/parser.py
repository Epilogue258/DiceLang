from typing import Self, cast  # cast可以用于收紧类型

from .astnode import (
    AstNode,
    BinaryOpNode,
    DiceNode,
    FuncCallNode,
    GroupNode,
    NumberNode,
    SelectorNode,
    UnaryOpNode,
)  # TODO 确保应导尽导
from .error import ParserError, TodoError
from .statement import ErrorStmt, ExprStmt, MacroDefStmt, Statement, VarDefStmt
from .tokens import Token, TokenType


class Parser:  # TODO 解析器：输入 Token 流，输出 AST（抽象语法树）。
    def __init__(self, tokens: list[Token] | None = None):
        self.tokens = tokens if tokens is not None else []
        self.pos = 0

        if self.tokens and self.tokens[-1].type != TokenType.EOF:
            raise ParserError("Token流必须以EOF结尾", token=self.tokens[-1] if self.tokens else None)

        # self.ast: AstNode = self.parse_expr()  # TODO DEL 先把表达式解析做好，日后再添加变量定义、宏定义等其他语句类型

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
                    f"期望 {expected_type}, 得到类型为: {self.current.type} 位于 {self.current.pos}, 内容为: {self.current.text}",
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

    def parse(self, tokens: list[Token] | None = None) -> Statement:
        if tokens is not None:
            self.tokens = tokens
            self.pos = 0
        if self.tokens is None:
            raise ParserError("没有提供Token流")
        try:
            return ExprStmt(value=self.parse_expr())  # TODO 先把表达式语句做好，日后再添加变量定义、宏定义等其他语句类型
        except ParserError as e:
            return ErrorStmt(value=e)

    def prefix_parse(self, token: Token) -> AstNode:
        match token.type:
            case TokenType.NUMBER:
                return NumberNode(value=token.value)
            case TokenType.PLUS | TokenType.MINUS:
                bp = cast(int, self.get_prefix_bp(token))  # 同类型检查器搏斗的产物
                operand = self.parse_expr(bp)
                return UnaryOpNode(op=token.type, operand=operand)
            case TokenType.IDENTIFIER:
                if self.match(TokenType.LPAREN):
                    # FuncCallNode Start
                    group = self._parse_delimited(start=TokenType.LPAREN)
                    if not group:
                        raise ParserError("括号内不存在任何可被解析的值", tokens=self.tokens)
                    return FuncCallNode(
                        func=token.text, args=GroupNode(group=group), pos=token.pos, length=len(token.text + str(group))
                    )

                else:  # VarNode Start
                    raise TodoError("变量功能尚未实现")

            case TokenType.LPAREN:  # Return: GroupNode | FuncCallNode TODO: 验证函数调用是否可行
                if self.match(TokenType.RPAREN):
                    raise ParserError("括号内不存在任何可被解析的值", tokens=self.tokens)
                group = self._parse_delimited()
                if len(group) > 1:
                    raise ParserError("参数过多", group=group, length=len(group))
                return GroupNode(group=group)

            case TokenType.EOF:
                raise ParserError("表达式不完整意, 外到达文件结尾", token=token, pos=token.pos)
            case _:
                raise ParserError(
                    f"不能将「{token}」当作前缀运算符, 请检查是否遗漏运算符。",
                    token=token,
                )

    def infix_parse(self, left: AstNode, op_token: Token, right_bp: int) -> AstNode:
        match op_token.type:
            case TokenType.PLUS | TokenType.MINUS | TokenType.MULTIPLY | TokenType.DIVIDE | TokenType.POW | TokenType.MOD:
                right = self.parse_expr(right_bp)
                return BinaryOpNode(op=op_token.type, left=left, right=right)
            case TokenType.DICE:
                right = self.parse_expr(right_bp)
                return DiceNode(count=left, sides=right, selectors=[])  # TODO selectors
            case TokenType.LPAREN:
                raise ParserError(
                    f"遇到了意外的Token: “{op_token.text}”, 可能缺少括号间的运算符",
                    token=op_token,
                    pos=op_token.pos,
                )
            case TokenType.RPAREN:
                raise ParserError("多余了右括号。", pos=op_token.pos)
            case _:  # TODO：日后可以添加用户自定义字典
                raise ParserError(f"不支持的中缀操作: {op_token.type}, 位于{op_token.pos}, 内容: {op_token.text}")

    def parse_expr(self, min_bp: int = 0) -> AstNode:
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
            if infix_bp is None:
                raise ParserError(f"不能将「{op_token}」当作中缀运算符, 请检查是否遗漏运算符。")

            left_bp, right_bp = infix_bp
            if left_bp < min_bp:
                break

            self.consume()  # 消耗中缀——在之前消耗的话会出现pos越界的情况，有点危险。

            left = self.infix_parse(left, op_token, right_bp)
        return left

    def _parse_delimited(
        self,
        *,
        start: TokenType | None = None,
        end: TokenType = TokenType.RPAREN,
        delimiter: TokenType = TokenType.COMMA,
    ) -> list[AstNode]:

        if start is not None:
            self.expect(
                start,
                error=ParserError(f"期望 {start}, 得到 {self.current.type}", token=self.current),
            ).consume()

        min_bp = infix_parselets[end][0] + 1
        if min_bp < infix_parselets[delimiter][0]:
            raise ParserError(
                f"delimiter的绑定力小于end的绑定力, delimiter: {infix_parselets[delimiter][0]}, end: {infix_parselets[end][0]}"
            )
        group = []

        while not self.match(end, TokenType.EOF):  # 说明解析后抵达的可能是delimiter而非end
            group.append(self.parse_expr(min_bp))  # 无论delimiter的绑定力为何，加1来确保解析到delimiter时中止解析。
            if self.match(delimiter):
                self.consume()

        self.expect(
            end,
            error=ParserError(
                f"遇到了意外的Token: “ {self.current} ”而非{end}。",
                token=self.current,
                pos=self.current.pos,
            ),
        ).consume()

        return group

    # TODO DEL
    # def __str__(self):
    #     # 这其实没什么用，和Lexer做个语义对齐而已
    #     return f"<Parser: {self.ast}>" if self.ast else "<Parser: empty>"


# --- 优先级表 ---
prefix_parselets = {
    TokenType.PLUS: 50,  # 一元加
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
    TokenType.RPAREN: (0, 0),
    TokenType.COMMA: (0, 0),
    TokenType.EOF: (-1, -1),
}

if __name__ == "__main__":  # pragma: no cover  # TODO 测试用
    from .lexer import Lexer

    sounce = "1+2*2**5d6-4*(3+5)"
    tokens = Lexer.tokenize(sounce)

    print(f"\nTokens: {Lexer.format_tokens(tokens)}\n")
    parser = Parser(tokens)

    # assert eval(sounce) == eval(str(parser.ast))
