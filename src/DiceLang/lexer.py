from collections.abc import Callable

from .tokens import (
    Token,
    TokenType,
)


class Lexer:  # 词法分析器：输入字符串，输出 Token 流。
    def __init__(self, text: str):
        self.tokens: list[Token] = self.tokenize(text)

    def tokenize(self, text: str) -> list[Token]:
        index = 0
        tokens = []
        while index < len(text):
            ch = text[index]
            if ch.isspace():
                index += 1
                continue
            elif ch.isdigit():
                num = _consume_while(str.isdigit, text, index)
                tokens.append(Token(TokenType.NUMBER, int(num), num, index))
                index += len(num)
            elif ch.isalpha():
                identifier = _consume_while(str.isalpha, text, index)
                end_pos = index + len(identifier)
                if identifier.lower() in IDENTIFIER_TO_TYPE:
                    # 把dhkltr等lower, 标准化为1d6等, 这是为了同函数保持一致, 严格来说D这种大写其实更好
                    tokens.append(Token(IDENTIFIER_TO_TYPE[identifier.lower()], identifier.lower(), identifier, index))
                else:  # 说不定是自定义变量, 而查询token是否存在并非Lexer的任务, 不然x = 5报错也太滑稽了
                    tokens.append(Token(TokenType.IDENTIFIER, identifier.lower(), identifier, index))
                index = end_pos
            elif ch in SYMBOLS:
                # 注意SYMBOLS和SYMBOL_TO_TYPE的区别, 前者是符号集合, 比如尽管不存在!这个token, 由于其为!=的一部分,in SYMBOLS为真
                symbol = _consume_while(lambda c: c in SYMBOLS, text, index, max_length=LONGEST_SYMBOL_LENGTH)
                # 然后, 对于1-(2), 会匹配成-(, 这时就需要回退到-
                while symbol not in SYMBOL_TO_TYPE and len(symbol) > 1:
                    symbol = symbol[:-1]  # 对于上述例子, 这里回退后symbol变作-, (会在下次循环捕获, 如此实现最长匹配
                end_pos = index + len(symbol)
                if symbol in SYMBOL_TO_TYPE:
                    tokens.append(Token(SYMBOL_TO_TYPE[symbol], _standardize_symbol(symbol), symbol, index))
                else:
                    raise ValueError(f"未知的符号: {symbol} 位于索引{index}到{end_pos}部分")
                index = end_pos
            else:
                raise ValueError(f"未知的字符: {ch} 位于索引{index}部分")
        # while index < len(text): ends
        tokens.append(Token(TokenType.EOF, None, "", -1))
        return tokens

    def __str__(self):
        # 令人难堪的是，python的list自动调用的是repr，故而即使print(f"{tokens}")而非{tokens！r}，其结果可能也会令你错愕

        tokens = " ".join(map(str, self.tokens))
        return f"<Lexer: {tokens}>" if tokens else "<Lexer: empty>"


IDENTIFIER_TO_TYPE: dict[str, TokenType] = {
    "d": TokenType.DICE,
    "h": TokenType.HIGHEST,
    "l": TokenType.LOWEST,
    "k": TokenType.KEEP,
    "t": TokenType.THROW,
    "e": TokenType.EXPLODE,
    "c": TokenType.COUNT,
    "if": TokenType.IF,
    "ifc": TokenType.IFCOUNT,
}

SYMBOL_TO_TYPE: dict[str, TokenType] = {
    # 双字符运算符（注意顺序不重要，但消费时要按最长匹配）
    "**": TokenType.POW,
    "==": TokenType.EQ,
    "!=": TokenType.NEQ,
    "<=": TokenType.LTE,
    ">=": TokenType.GTE,
    "//": TokenType.DIVIDE,  # 归一化，我们毕竟不需要小数
    # 单字符运算符
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MULTIPLY,
    "/": TokenType.DIVIDE,
    "%": TokenType.MOD,
    "^": TokenType.POW,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "=": TokenType.ASSIGN,
    "!": TokenType.EXPLODE,  # 爆炸骰
    ":": TokenType.COLON,
}

STANDARD_SYMBOLS: dict[str, str] = {
    "**": "^",
    "e": "!",
}

LONGEST_SYMBOL_LENGTH = max(len(sym) for sym in SYMBOL_TO_TYPE)  # 有趣的是，python直接取用默认获取的是key而无需解包

SYMBOLS = frozenset("".join(SYMBOL_TO_TYPE.keys()))


def _consume_while(predicate: Callable[[str], bool], text: str, pos: int, max_length: int | None = None) -> str:
    result = ""
    while pos < len(text) and predicate(text[pos]):
        result += text[pos]
        pos += 1
        if max_length is not None and len(result) >= max_length:
            break
    return result


def _standardize_symbol(symbol: str) -> str:
    return STANDARD_SYMBOLS.get(symbol, symbol)
