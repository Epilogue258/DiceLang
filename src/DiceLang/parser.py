from typing import Self, cast  # cast可以用于收紧类型

from .astnode import (
    AstNode,
    BinaryOpNode,
    ConditionMod,
    CountMod,
    DiceNode,
    FuncCallNode,
    GroupNode,
    HighestMod,
    KeepMod,
    LowestMod,
    MacroRefNode,
    MapMod,
    ModifierNode,
    NumberNode,
    ThrowMod,
    UnaryOpNode,
    VarNode,
)  # TODO 确保应导尽导
from .error import ParserError, TodoError
from .statement import ErrorStmt, ExprStmt, MacroDefStmt, Statement, VarDefStmt
from .tokens import Token, TokenType

# 所有赋值操作符
_ASSIGN_OPS = frozenset(
    {
        TokenType.ASSIGN,
        TokenType.PLUS_ASSIGN,
        TokenType.MINUS_ASSIGN,
        TokenType.MULTIPLY_ASSIGN,
        TokenType.DIVIDE_ASSIGN,
        TokenType.MOD_ASSIGN,
        TokenType.POW_ASSIGN,
    }
)

# if / ifc 的条件运算符集合
_COND_TOKENS = frozenset(
    {
        TokenType.GT,
        TokenType.LT,
        TokenType.GTE,
        TokenType.LTE,
        TokenType.EQ,
        TokenType.NEQ,
    }
)

# 不能作为变量名的关键字
_KEYWORDS = frozenset(
    {
        TokenType.HIGHEST,
        TokenType.LOWEST,
        TokenType.KEEP,
        TokenType.THROW,
        TokenType.IF,
        TokenType.IFCOUNT,
        TokenType.COUNT,
        TokenType.DICE,
        TokenType.EXPLODE,
    }
)


class Parser:
    BP_MAX = 999  # 选择器参数绑定力上限，阻止意外吃入后续 token

    def __init__(self, tokens: list[Token] | None = None):
        self.tokens = tokens if tokens is not None else []
        self.pos = 0

        if self.tokens and self.tokens[-1].type != TokenType.EOF:
            raise ParserError("Token流必须以EOF结尾", token=self.tokens and self.tokens[-1])

    @property
    def current(self) -> Token:
        """总是返回当前指针指向的 Token"""
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
                    f"期望 {expected_type}, 得到类型为: {self.peek(offset).type} 位于 {self.peek(offset).pos}, 内容为: {self.peek(offset).text}",
                    token=self.peek(offset),
                    pos=self.peek(offset).pos,
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
            return self.parse_to_stmt()
        except ParserError as e:
            return ErrorStmt(value=e)

    def _scan_def_names(self) -> tuple[int, tuple[str, ...], TokenType] | None:
        """无副作用扫描 IDENTIFIER (, IDENTIFIER)* OP。
        成功返回 (消费数, 名字元组, 赋值操作符)，失败返回 None 且不移动 pos。
        遇到关键字直接抛 ParserError。
        """
        offset = 0
        names: list[str] = []
        while True:
            t = self.peek(offset)
            if t.type == TokenType.IDENTIFIER:
                names.append(t.value)
                offset += 1
            elif t.type == TokenType.COMMA and names:
                offset += 1
            elif t.type in _ASSIGN_OPS and names:
                return offset + 1, tuple(names), t.type
            elif t.type in _KEYWORDS:
                raise ParserError(f"{t.text} 是关键字，无法命名", token=t)
            else:
                return None

    def parse_to_stmt(self) -> Statement:
        # MacroDef: & a, b, c = expr
        if self.current.type == TokenType.MACRO:
            self.consume()  # 消费 &
            info = self._scan_def_names()
            if info is None:
                raise ParserError("宏定义缺少名称", token=self.current)
            consume_count, names, op = info
            if op != TokenType.ASSIGN:
                raise ParserError("宏定义仅支持 = 赋值", token=self.current)
            for _ in range(consume_count):
                self.consume()
            return MacroDefStmt(names=names, expr=self.parse_expr())

        # VarDef: IDENTIFIER (, IDENTIFIER)* OP expr
        info = self._scan_def_names()
        if info is not None:
            consume_count, names, op = info
            for _ in range(consume_count):
                self.consume()
            return VarDefStmt(names=names, expr=self.parse_expr(), op=op)

        # 默认：表达式语句
        if self.tokens:
            return ExprStmt(value=self.parse_expr())
        raise SyntaxError("无 Token 可解析")

    def prefix_parse(self, token: Token) -> AstNode:
        match token.type:
            case TokenType.NUMBER:
                return NumberNode(value=token.value, pos=token.pos, length=len(token.text))
            case TokenType.PLUS | TokenType.MINUS:
                bp = cast(int, self.get_prefix_bp(token))  # 同类型检查器搏斗的产物
                operand = self.parse_expr(bp)
                return UnaryOpNode(op=token.type, operand=operand, pos=token.pos, length=len(token.text))
            case TokenType.IDENTIFIER:
                if self.match(TokenType.LPAREN):
                    group = self._parse_delimited(start=TokenType.LPAREN)
                    if not group:
                        raise ParserError("括号内不存在任何可被解析的值", token=token)
                    return FuncCallNode(
                        func=token.text, args=GroupNode(group=group), pos=token.pos, length=len(token.text + str(group))
                    )
                else:  # VarNode
                    return VarNode(name=token.value, pos=token.pos, length=len(token.text))
            case TokenType.LPAREN:
                if self.match(TokenType.RPAREN):
                    raise ParserError("括号内不存在任何可被解析的值", token=token)
                group = self._parse_delimited()
                if len(group) > 1:
                    raise ParserError("参数过多", token=token, group=group)
                return GroupNode(group=group, pos=token.pos, length=None)  # length 由内容决定
            case TokenType.MACRO:
                ident = self.expect(TokenType.IDENTIFIER, error=ParserError("宏引用必须跟随标识符", token=self.peek())).consume()
                return MacroRefNode(name=ident.value, pos=token.pos, length=len(token.text) + len(ident.text))
            case TokenType.EOF:
                raise ParserError("表达式不完整，意外到达文件结尾", token=token)
            case _:
                raise ParserError(
                    f"不能将「{token}」当作前缀运算符, 请检查是否遗漏运算符。",
                    token=token,
                )

    def infix_parse(self, left: AstNode, op_token: Token, right_bp: int) -> AstNode:
        match op_token.type:
            case TokenType.PLUS | TokenType.MINUS | TokenType.MULTIPLY | TokenType.DIVIDE | TokenType.POW | TokenType.MOD:
                right = self.parse_expr(right_bp)
                return BinaryOpNode(op=op_token.type, left=left, right=right, pos=op_token.pos, length=len(op_token.text))
            case TokenType.DICE:
                right = self.parse_expr(right_bp)
                return DiceNode(count=left, sides=right, selectors=self._parse_selectors(), pos=op_token.pos, length=len(op_token.text))
            case TokenType.LPAREN:
                raise ParserError(
                    f"遇到了意外的Token: “{op_token.text}”, 可能缺少括号间的运算符",
                    token=op_token,
                )
            case TokenType.RPAREN:
                raise ParserError("多余了右括号。", token=op_token)
            case _:  # TODO：日后可以添加用户自定义字典
                raise ParserError(
                    f"不支持的中缀操作: {op_token.type}, 位于{op_token.pos}, 内容: {op_token.text}",
                    token=op_token,
                )

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
                raise ParserError(f"不能将「{op_token}」当作中缀运算符, 请检查是否遗漏运算符。", token=op_token)

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

    def _parse_selectors(self) -> list[ModifierNode]:
        """解析骰子后缀选择器链。"""
        selectors: list[ModifierNode] = []
        while True:
            match self.current.type:
                case TokenType.HIGHEST:
                    op = self.consume()
                    selectors.append(HighestMod(count=self.parse_expr(self.BP_MAX), pos=op.pos, length=len(op.text)))
                case TokenType.LOWEST:
                    op = self.consume()
                    selectors.append(LowestMod(count=self.parse_expr(self.BP_MAX), pos=op.pos, length=len(op.text)))
                case TokenType.KEEP:
                    op = self.consume()
                    selectors.append(KeepMod(pos=op.pos, length=len(op.text)))
                case TokenType.THROW:
                    op = self.consume()
                    selectors.append(ThrowMod(pos=op.pos, length=len(op.text)))
                case TokenType.IF | TokenType.IFCOUNT:
                    op = self.consume()
                    cond = self.consume()
                    if cond.type not in _COND_TOKENS:
                        raise ParserError(f"if 后应为比较运算符，得到 {cond.text}", token=cond)
                    threshold = self.parse_expr(self.BP_MAX)
                    selectors.append(ConditionMod(condition=cond.type, threshold=threshold, pos=op.pos, length=len(op.text)))
                    if op.type == TokenType.IFCOUNT:
                        # pos/len 指向 ifc 关键字，否则报错时无法标红源码位置
                        selectors.append(CountMod(pos=op.pos, length=len(op.text), is_ifc=True))
                case TokenType.COUNT:
                    op = self.consume()
                    selectors.append(CountMod(pos=op.pos, length=len(op.text)))
                case TokenType.COLON:
                    op = self.consume()
                    selectors.append(MapMod(map_to=self.parse_expr(self.BP_MAX), pos=op.pos, length=len(op.text)))
                case _:
                    break
        return selectors


# --- 优先级表 ---
prefix_parselets = {
    TokenType.PLUS: 50,  # 一元加
    TokenType.MINUS: 50,  # 一元减
    TokenType.DICE: 60,  # 缺省骰 d6 = 1d6
    TokenType.MACRO: 50,  # 宏引用
    # LPAREN 不需要绑定力，因为它是硬编码的特殊处理
}

infix_parselets: dict[TokenType, tuple[int, int]] = {
    TokenType.PLUS: (10, 11),
    TokenType.MINUS: (10, 11),
    TokenType.MULTIPLY: (20, 21),
    TokenType.DIVIDE: (20, 21),
    TokenType.MOD: (20, 21),
    TokenType.POW: (31, 30),  # 右结合幂运算 2^3^4 -> 2^(3^4)
    TokenType.HIGHEST: (60, 61),
    TokenType.LOWEST: (60, 61),
    TokenType.KEEP: (60, 61),
    TokenType.THROW: (60, 61),
    TokenType.IF: (60, 61),
    TokenType.IFCOUNT: (60, 61),
    TokenType.COUNT: (60, 61),
    TokenType.COLON: (60, 61),
    TokenType.DICE: (70, 71),  # 骰子 bp 高于选择器，阻止选择器被骰子面数误吞
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
