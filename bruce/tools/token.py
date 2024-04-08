from .grammar import Terminal


class Token:
    def __init__(
        self, lex: str, token_type: Terminal, line: str = None, column: str = None
    ):
        self.lex = lex
        self.token_type = token_type
        self.position = (line, column)

    def __str__(self):
        return f"{self.token_type}: {self.lex}"

    def __repr__(self):
        return str(self)

    @property
    def is_valid(self):
        return True
