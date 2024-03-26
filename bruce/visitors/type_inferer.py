from ..tools import visitor


class TypeInferer:
    def __init__(self):
        self.errors: list[str] = []
        self.occurs = False

    @visitor.on("node")
    def visit(self, node, ctx, scope):
        pass


# PD: I AM COOKING HERE...
