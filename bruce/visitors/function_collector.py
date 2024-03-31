from ..tools import visitor
from ..tools.semantic import SemanticError
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from .. import ast


class FunctionCollector:
    def __init__(self):
        self.errors: list[str] = []

    @visitor.on("node")
    def visit(self, node, ctx, scope):
        pass

    @visitor.when(ast.FunctionNode)
    def visit(self, node: ast.FunctionNode, ctx: Context, scope: Scope):
        params = []
        for n, t in node.params:
            try:
                pt = get_safe_type(t, ctx)
            except SemanticError as se:
                self.errors.append(se.text)
            else:
                params.append((n, pt))

        rt = None
        try:
            rt = get_safe_type(node.return_type, ctx)
        except SemanticError as se:
            self.errors.append(se.text)

        if scope.is_func_defined(node.id):
            self.errors.append(f"Function '{node.id}' already exists in scope.")
        else:
            scope.define_function(node.id, params, rt)

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, ctx: Context, scope: Scope):
        for decl in node.declarations:
            if isinstance(decl, ast.FunctionNode):
                self.visit(decl, ctx, scope)

        return self.errors
