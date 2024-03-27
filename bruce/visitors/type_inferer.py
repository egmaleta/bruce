from typing import Union

from ..tools import visitor
from ..tools.semantic import Type, Proto
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from .. import ast
from .. import types


class TypeInferer:
    def __init__(self):
        self.errors: list[str] = []
        self.occurs = False

    def _infer(self, node: ast.ExprNode, scope: Scope, new_type: Union[Type, Proto]):
        if isinstance(node, ast.IdentifierNode):
            var = scope.find_variable(node.value)

            if var.type is None:
                var.set_type(new_type)
                self.occurs = True

            elif isinstance(var.type, types.UnionType):
                itsc = var.type & new_type
                l = len(itsc)
                if 0 < l < len(var.type):
                    self.occurs = True

                    if l == 1:
                        t, *_ = itsc
                        var.set_type(t)
                    else:
                        var.set_type(itsc)

    @visitor.on("node")
    def visit(self, node, ctx, scope):
        pass

    @visitor.when(ast.NumberNode)
    def visit(self, node: ast.NumberNode, ctx: Context, scope: Scope):
        return types.NUMBER_TYPE

    @visitor.when(ast.StringNode)
    def visit(self, node: ast.StringNode, ctx: Context, scope: Scope):
        return types.STRING_TYPE

    @visitor.when(ast.BooleanNode)
    def visit(self, node: ast.BooleanNode, ctx: Context, scope: Scope):
        return types.BOOLEAN_TYPE

    @visitor.when(ast.IdentifierNode)
    def visit(self, node: ast.IdentifierNode, ctx: Context, scope: Scope):
        if node.is_builtin and node.value == "base":
            return types.FUNCTION_TYPE

        var = scope.find_variable(node.value)
        if var is not None:
            return var.type

        return types.FUNCTION_TYPE

    @visitor.when(ast.TypeInstancingNode)
    def visit(self, node: ast.TypeInstancingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.VectorNode)
    def visit(self, node: ast.VectorNode, ctx: Context, scope: Scope):
        item_types = []
        for expr in node.items:
            t = self.visit(expr, ctx, scope)
            if t is not None:
                item_types.append(t)

        if len(item_types) > 0:
            ut = types.UnionType(*item_types)
            for expr in node.items:
                self._infer(expr, scope, ut)

            return types.VectorType(ut)

        return types.VectorType(types.OBJECT_TYPE)

    @visitor.when(ast.MappedIterableNode)
    def visit(self, node: ast.MappedIterableNode, ctx: Context, scope: Scope):
        t = get_safe_type(node.item_type, ctx)
        iterable_t = self.visit(node, ctx, scope)

        if t is None:
            if isinstance(iterable_t, types.VectorType):
                t = iterable_t.item_type
            elif isinstance(iterable_t, Type) and iterable_t.implements(
                types.ITERABLE_PROTO
            ):
                # t = ...
                pass
            elif iterable_t == types.ITERABLE_PROTO:
                t = types.OBJECT_TYPE

        child_scope = scope.create_child()
        child_scope.define_variable(node.item_id, t)
        mapped_t = self.visit(node.map_expr, ctx, child_scope)

        return types.VectorType(mapped_t if mapped_t is not None else types.OBJECT_TYPE)

    @visitor.when(ast.MemberAccessingNode)
    def visit(self, node: ast.MemberAccessingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.FunctionCallNode)
    def visit(self, node: ast.FunctionCallNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.IndexingNode)
    def visit(self, node: ast.IndexingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.MutationNode)
    def visit(self, node: ast.MutationNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.DowncastingNode)
    def visit(self, node: ast.DowncastingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.NegOpNode)
    def visit(self, node: ast.NegOpNode, ctx: Context, scope: Scope):
        t = self.visit(node.operand, ctx, scope)

        self._infer(node.operand, scope, types.BOOLEAN_TYPE)

        return types.BOOLEAN_TYPE

    @visitor.when(ast.ArithNegOpNode)
    def visit(self, node: ast.ArithNegOpNode, ctx: Context, scope: Scope):
        t = self.visit(node.operand, ctx, scope)

        self._infer(node.operand, scope, types.NUMBER_TYPE)

        return types.NUMBER_TYPE

    @visitor.when(ast.LogicOpNode)
    def visit(self, node: ast.LogicOpNode, ctx: Context, scope: Scope):
        self.visit(node.left, ctx, scope)
        self.visit(node.right, ctx, scope)

        self._infer(node.left, scope, types.BOOLEAN_TYPE)
        self._infer(node.right, scope, types.BOOLEAN_TYPE)

        return types.BOOLEAN_TYPE

    @visitor.when(ast.ComparisonOpNode)
    def visit(self, node: ast.ComparisonOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.ArithOpNode)
    def visit(self, node: ast.ArithOpNode, ctx: Context, scope: Scope):
        self.visit(node.left, ctx, scope)
        self.visit(node.right, ctx, scope)

        self._infer(node.left, scope, types.NUMBER_TYPE)
        self._infer(node.right, scope, types.NUMBER_TYPE)

        return types.NUMBER_TYPE

    @visitor.when(ast.ConcatOpNode)
    def visit(self, node: ast.ConcatOpNode, ctx: Context, scope: Scope):
        self.visit(node.left, ctx, scope)
        self.visit(node.right, ctx, scope)

        ut = types.UnionType(types.NUMBER_TYPE, types.STRING_TYPE)
        self._infer(node.left, scope, ut)
        self._infer(node.right, scope, ut)

        return types.STRING_TYPE

    @visitor.when(ast.TypeMatchingNode)
    def visit(self, node: ast.TypeMatchingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.LoopNode)
    def visit(self, node: ast.LoopNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.IteratorNode)
    def visit(self, node: ast.IteratorNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.LetExprNode)
    def visit(self, node: ast.LetExprNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.FunctionNode)
    def visit(self, node: ast.FunctionNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.ProtocolNode)
    def visit(self, node: ast.ProtocolNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.TypeNode)
    def visit(self, node: ast.TypeNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, ctx: Context, scope: Scope):
        pass


# PD: I AM COOKING HERE...
