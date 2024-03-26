from ..tools import visitor
from ..tools.semantic.context import Context
from ..tools.semantic.scope import Scope
from .. import ast
from .. import types


class TypeInferer:
    def __init__(self):
        self.errors: list[str] = []
        self.occurs = False

    @visitor.on("node")
    def visit(self, node, ctx, scope):
        pass

    @visitor.on(ast.NumberNode)
    def visit(self, node, ctx, scope):
        return types.NUMBER_TYPE

    @visitor.on(ast.StringNode)
    def visit(self, node, ctx, scope):
        return types.STRING_TYPE

    @visitor.on(ast.BooleanNode)
    def visit(self, node, ctx, scope):
        return types.BOOLEAN_TYPE


# PD: I AM COOKING HERE...
