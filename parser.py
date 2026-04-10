from tokens import Token, TokenType
class Parser: # TODO 解析器：输入 Token 流，输出 AST（抽象语法树）。
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

        if tokens and tokens[-1].type != TokenType.EOF:
            raise ValueError("Token流必须以EOF结尾")
    
    @property
    def current(self) -> Token:
        # 总是返回当前指针指向的 Token
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, None, "", -1)

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, None, "", -1)

    def consume(self, expected_type: TokenType | None = None) -> Token:
        # 确认并移动指针
        token = self.current
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"期望 {expected_type}, 得到 {token.type} at {token.pos}")
        self.pos += 1
        return token
    
    def parse(self):
        token = self.current
        if token.type in (...):
            pass