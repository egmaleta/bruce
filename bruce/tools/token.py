from .grammar import Terminal


class Token:
    def __init__(self, lex: str, token_type: Terminal):
        self.lex = lex
        self.token_type = token_type

    def __str__(self):
        return f"{self.token_type}: {self.lex}"

    def __repr__(self):
        return str(self)

    @property
    def is_valid(self):
        return True
