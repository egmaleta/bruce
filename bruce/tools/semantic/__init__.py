from abc import ABC


class ASTNode(ABC):
    pass


class SemanticError(Exception):
    @property
    def text(self):
        return self.args[0]
