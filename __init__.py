# DiceLang/__init__.py

# TODO 从子模块里把最常用的类引进来
from .lexer import Lexer
from .parser import Parser
from .evaluator import Evaluator
from .tokens import Token, TokenType

__version__ = "0.1.0"