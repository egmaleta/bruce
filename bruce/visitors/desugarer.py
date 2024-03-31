from ..tools import visitor
from .. import ast
from ..names import NEXT_METHOD_NAME, CURRENT_METHOD_NAME


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

        self.current_method_name: str | None = None
        self.current_type_parent_name: str | None = None

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
            "Iterable",
            iterable_expr,
            ast.LoopNode(
                ast.FunctionCallNode(
                    ast.MemberAccessingNode(
                        ast.IdentifierNode(iterable_id), NEXT_METHOD_NAME
                    ),
                    [],
                ),
                ast.LetExprNode(
                    node.item_id,
                    node.item_type,
                    ast.FunctionCallNode(
                        ast.MemberAccessingNode(
                            ast.IdentifierNode(iterable_id), CURRENT_METHOD_NAME
                        ),
                        [],
                    ),
                    body,
                ),
                fallback_expr,
            ),
        )

    @visitor.when(ast.LiteralNode)
    def visit(self, node: ast.LiteralNode):
        return node

    @visitor.when(ast.TypeInstancingNode)
    def visit(self, node: ast.TypeInstancingNode):
        return ast.TypeInstancingNode(node.type, [self.visit(arg) for arg in node.args])

    @visitor.when(ast.VectorNode)
    def visit(self, node: ast.VectorNode):
        return ast.VectorNode([self.visit(item) for item in node.items])

    @visitor.when(ast.MappedIterableNode)
    def visit(self, node: ast.MappedIterableNode):
        return ast.MappedIterableNode(
            self.visit(node.map_expr),
            node.item_id,
            node.item_type,
            self.visit(node.iterable_expr),
        )

    @visitor.when(ast.MemberAccessingNode)
    def visit(self, node: ast.MemberAccessingNode):
        return ast.MemberAccessingNode(self.visit(node.target), node.member_id)

    @visitor.when(ast.FunctionCallNode)
    def visit(self, node: ast.FunctionCallNode):
        return ast.FunctionCallNode(
            self.visit(node.target), [self.visit(arg) for arg in node.args]
        )

    @visitor.when(ast.IndexingNode)
    def visit(self, node: ast.IndexingNode):
        return ast.IndexingNode(self.visit(node.target), self.visit(node.index))

    @visitor.when(ast.MutationNode)
    def visit(self, node: ast.MutationNode):
        return ast.MutationNode(self.visit(node.target), self.visit(node.value))

    @visitor.when(ast.DowncastingNode)
    def visit(self, node: ast.DowncastingNode):
        return ast.DowncastingNode(self.visit(node.target), node.type)

    @visitor.when(ast.UnaryOpNode)
    def visit(self, node: ast.UnaryOpNode):
        return type(node)(self.visit(node.operand))

    @visitor.when(ast.BinaryOpNode)
    def visit(self, node: ast.BinaryOpNode):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node, (ast.PowerOpNode, ast.ConcatOpNode)):
            return type(node)(left, right)

        return type(node)(left, node.operator, right)

    @visitor.when(ast.TypeMatchingNode)
    def visit(self, node: ast.TypeMatchingNode):
        return ast.TypeMatchingNode(self.visit(node.target), node.type)

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode):
        return ast.BlockNode([self.visit(expr) for expr in node.exprs])

    @visitor.when(ast.LoopNode)
    def visit(self, node: ast.LoopNode):
        return ast.LoopNode(
            self.visit(node.condition),
            self.visit(node.body),
            self.visit(node.fallback_expr),
        )

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode):
        return ast.ConditionalNode(
            [(self.visit(c), self.visit(b)) for c, b in node.condition_branchs],
            self.visit(node.fallback_branch),
        )

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode):
        function_nodes: list[ast.FunctionNode] = []
        type_nodes: list[ast.TypeNode] = []

        for decl in node.declarations:
            if isinstance(decl, ast.FunctionNode):
                function_nodes.append(decl)
            elif isinstance(decl, ast.TypeNode):
                type_nodes.append(decl)

        for fn in function_nodes:
            fn.body = self.visit(fn.body)

        for tn in type_nodes:
            self.current_type_parent_name = tn.parent_type

            if tn.parent_args is not None:
                tn.parent_args = [self.visit(arg) for arg in tn.parent_args]

            for member in tn.members:
                if isinstance(member, ast.TypePropertyNode):
                    member.value = self.visit(member.value)
                elif isinstance(member, ast.FunctionNode):
                    self.current_method_name = member.id
                    member.body = self.visit(member.body)

        node.expr = self.visit(node.expr)

        return node
