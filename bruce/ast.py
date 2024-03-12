from .tools.semantic import AST
from .tools.token import Token


class Number(AST):
    def __init__(self, token: Token):
        self.value = token.lex
