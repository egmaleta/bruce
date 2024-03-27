from ..tools import visitor
from .. import ast


def desugar_let_expr(
    bindings: list[tuple[str, str | None, ast.ExprNode]], body: ast.ExprNode
):
    head, *tail = bindings
    id, type, value = head

    return ast.LetExprNode(
        id, type, value, body if len(tail) == 0 else desugar_let_expr(tail, body)
    )


class Desugarer:
    def __init__(self):
        self.iterable_count = 0

    def next_iterable_id(self):
        self.iterable_count += 1
        return f"$iterable_{self.iterable_count}"

    @visitor.on("node")
    def visit(self, node):
        pass

    @visitor.when(ast.MultipleLetExprNode)
    def visit(self, node: ast.MultipleLetExprNode):
        bindings = [(n, t, self.visit(v)) for n, t, v in node.bindings]
        body = self.visit(node.body)

        return desugar_let_expr(bindings, body)

    @visitor.when(ast.IteratorNode)
    def visit(self, node: ast.IteratorNode):
        iterable_id = self.next_iterable_id()

        iterable_expr = self.visit(node.iterable_expr)
        body = self.visit(node.body)
        fallback_expr = self.visit(node.fallback_expr)

        return ast.LetExprNode(
            iterable_id,
            None,
            iterable_expr,
            ast.LoopNode(
                ast.FunctionCallNode(
                    ast.MemberAccessingNode(ast.IdentifierNode(iterable_id), "next"), []
                ),
                ast.LetExprNode(
                    node.item_id,
                    node.item_type,
                    ast.FunctionCallNode(
                        ast.MemberAccessingNode(
                            ast.IdentifierNode(iterable_id), "current"
                        ),
                        [],
                    ),
                    body,
                ),
                fallback_expr,
            ),
        )
