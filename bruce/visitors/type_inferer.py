from typing import Union

from ..tools import visitor
from ..tools.semantic import Type, Proto, SemanticError, Method
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from .. import ast
from .. import types as t
from ..names import SIZE_METHOD_NAME, INSTANCE_NAME


class TypeInferer:
    def __init__(self):
        self.errors: list[str] = []
        self.occurs = False

        # set before read
        self.current_type: Type = None
        self.current_method: Method = None

    def _infer(self, node: ast.ExprNode, scope: Scope, new_type: Union[Type, Proto]):
        if isinstance(node, ast.IdentifierNode):
            var = scope.find_variable(node.value)

            if var.type is None:
                var.set_type(new_type)
                self.occurs = True

            elif isinstance(var.type, t.UnionType):
                itsc = var.type & new_type
                l = len(itsc)
                if 0 < l < len(var.type):
                    self.occurs = True

                    if l == 1:
                        type, *_ = itsc
                        var.set_type(type)
                    else:
                        var.set_type(itsc)

    @visitor.on("node")
    def visit(self, node, ctx, scope):
        pass

    @visitor.when(ast.NumberNode)
    def visit(self, node: ast.NumberNode, ctx: Context, scope: Scope):
        return t.NUMBER_TYPE

    @visitor.when(ast.StringNode)
    def visit(self, node: ast.StringNode, ctx: Context, scope: Scope):
        return t.STRING_TYPE

    @visitor.when(ast.BooleanNode)
    def visit(self, node: ast.BooleanNode, ctx: Context, scope: Scope):
        return t.BOOLEAN_TYPE

    @visitor.when(ast.IdentifierNode)
    def visit(self, node: ast.IdentifierNode, ctx: Context, scope: Scope):
        if node.value == INSTANCE_NAME:
            if node.value not in self.current_method.params:
                # 'self' refers to current type
                return self.current_type

        var = scope.find_variable(node.value)
        if var is not None:
            return var.type

        return t.FUNCTION_TYPE

    @visitor.when(ast.TypeInstancingNode)
    def visit(self, node: ast.TypeInstancingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.VectorNode)
    def visit(self, node: ast.VectorNode, ctx: Context, scope: Scope):
        item_types = []
        for expr in node.items:
            expr_t = self.visit(expr, ctx, scope)
            if expr_t is not None:
                item_types.append(expr_t)

        if len(item_types) > 0:
            ut = t.UnionType(*item_types)
            for expr in node.items:
                self._infer(expr, scope, ut)

            return t.VectorType(ut)

        return t.VectorType(t.OBJECT_TYPE)

    @visitor.when(ast.MappedIterableNode)
    def visit(self, node: ast.MappedIterableNode, ctx: Context, scope: Scope):
        it = get_safe_type(node.item_type, ctx)
        iterable_t = self.visit(node, ctx, scope)

        if it is None:
            if isinstance(iterable_t, t.VectorType):
                it = iterable_t.item_type
            elif isinstance(iterable_t, Type) and iterable_t.implements(
                t.ITERABLE_PROTO
            ):
                # it = ...
                pass
            elif iterable_t == t.ITERABLE_PROTO:
                it = t.OBJECT_TYPE

        child_scope = scope.create_child()
        child_scope.define_variable(node.item_id, it)
        mapped_t = self.visit(node.map_expr, ctx, child_scope)

        return t.VectorType(mapped_t if mapped_t is not None else t.OBJECT_TYPE)

    @visitor.when(ast.MemberAccessingNode)
    def visit(self, node: ast.MemberAccessingNode, ctx: Context, scope: Scope):
        self.visit(node.target, ctx, scope)

        if (
            isinstance(node.target, ast.IdentifierNode)
            and node.target.value == INSTANCE_NAME
            and node.target.value not in self.current_method.params
            and scope.find_variable(node.target.value).owner_scope.is_function_scope
        ):
            # 'self' is current type
            try:
                return self.current_type.get_attribute(node.member_id)
            except SemanticError:
                return t.FUNCTION_TYPE

        canditate_types = []

        if node.member_id == SIZE_METHOD_NAME:
            canditate_types.append(t.VectorType(t.OBJECT_TYPE))

        for type in ctx.types.values():
            try:
                type.get_method(node.member_id)
            except SemanticError:
                pass
            else:
                canditate_types.append(type)

        for proto in ctx.protocols.values():
            if any(ms.name == node.member_id for ms in proto.all_method_specs()):
                canditate_types.append(proto)

        ut = t.UnionType(*canditate_types)
        self._infer(node.target, scope, ut)

        return t.FUNCTION_TYPE

    @visitor.when(ast.FunctionCallNode)
    def visit(self, node: ast.FunctionCallNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.IndexingNode)
    def visit(self, node: ast.IndexingNode, ctx: Context, scope: Scope):
        tt = self.visit(node.target, ctx, scope)
        self.visit(node.index, ctx, scope)

        if isinstance(tt, t.VectorType):
            return tt.item_type

        self._infer(node.target, scope, t.VectorType(t.OBJECT_TYPE))
        return t.OBJECT_TYPE

    @visitor.when(ast.MutationNode)
    def visit(self, node: ast.MutationNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ast.DowncastingNode)
    def visit(self, node: ast.DowncastingNode, ctx: Context, scope: Scope):
        self.visit(node.target, ctx, scope)

        return get_safe_type(node.type, ctx)

    @visitor.when(ast.NegOpNode)
    def visit(self, node: ast.NegOpNode, ctx: Context, scope: Scope):
        self.visit(node.operand, ctx, scope)

        self._infer(node.operand, scope, t.BOOLEAN_TYPE)

        return t.BOOLEAN_TYPE

    @visitor.when(ast.ArithNegOpNode)
    def visit(self, node: ast.ArithNegOpNode, ctx: Context, scope: Scope):
        self.visit(node.operand, ctx, scope)

        self._infer(node.operand, scope, t.NUMBER_TYPE)

        return t.NUMBER_TYPE

    @visitor.when(ast.LogicOpNode)
    def visit(self, node: ast.LogicOpNode, ctx: Context, scope: Scope):
        self.visit(node.left, ctx, scope)
        self.visit(node.right, ctx, scope)

        self._infer(node.left, scope, t.BOOLEAN_TYPE)
        self._infer(node.right, scope, t.BOOLEAN_TYPE)

        return t.BOOLEAN_TYPE

    @visitor.when(ast.ComparisonOpNode)
    def visit(self, node: ast.ComparisonOpNode, ctx: Context, scope: Scope):
        lt = self.visit(node.left, ctx, scope)
        rt = self.visit(node.right, ctx, scope)

        if node.operator not in ("==", "!="):
            if (lt == t.NUMBER_TYPE or lt == t.STRING_TYPE) and (
                rt is None or isinstance(rt, t.UnionType)
            ):
                self._infer(node.right, scope, lt)
            elif (rt == t.NUMBER_TYPE or rt == t.STRING_TYPE) and (
                lt is None or isinstance(lt, t.UnionType)
            ):
                self._infer(node.left, scope, rt)
            else:
                ut = t.UnionType(t.NUMBER_TYPE, t.STRING_TYPE)
                self._infer(node.left, scope, ut)
                self._infer(node.right, scope, ut)
        else:
            # NOT FOR NOW
            pass

        return t.BOOLEAN_TYPE

    @visitor.when(ast.ArithOpNode)
    def visit(self, node: ast.ArithOpNode, ctx: Context, scope: Scope):
        self.visit(node.left, ctx, scope)
        self.visit(node.right, ctx, scope)

        self._infer(node.left, scope, t.NUMBER_TYPE)
        self._infer(node.right, scope, t.NUMBER_TYPE)

        return t.NUMBER_TYPE

    @visitor.when(ast.ConcatOpNode)
    def visit(self, node: ast.ConcatOpNode, ctx: Context, scope: Scope):
        self.visit(node.left, ctx, scope)
        self.visit(node.right, ctx, scope)

        ut = t.UnionType(t.NUMBER_TYPE, t.STRING_TYPE)
        self._infer(node.left, scope, ut)
        self._infer(node.right, scope, ut)

        return t.STRING_TYPE

    @visitor.when(ast.TypeMatchingNode)
    def visit(self, node: ast.TypeMatchingNode, ctx: Context, scope: Scope):
        self.visit(node.target, ctx, scope)

        return t.BOOLEAN_TYPE

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, ctx: Context, scope: Scope):
        type = None
        for expr in node.exprs:
            type = self.visit(expr, ctx, scope.create_child())

        return type

    @visitor.when(ast.LoopNode)
    def visit(self, node: ast.LoopNode, ctx: Context, scope: Scope):
        self.visit(node.condition, ctx, scope)
        bt = self.visit(node.body, ctx, scope)
        ft = self.visit(node.fallback_expr, ctx, scope)

        self._infer(node.condition, scope, t.BOOLEAN_TYPE)

        if bt is None or ft is None:
            return None

        return bt if bt == ft else t.UnionType(bt, ft)

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, ctx: Context, scope: Scope):
        branch_types = []

        for cond, branch in node.condition_branchs:
            self.visit(cond, ctx, scope)

            bt = self.visit(branch, ctx, scope)
            branch_types.append(bt)

        ft = self.visit(node.fallback_branch, ctx, scope)
        branch_types.append(ft)

        for cond, _ in node.condition_branchs:
            self._infer(cond, scope, t.BOOLEAN_TYPE)

        if any(bt is None for bt in branch_types):
            return None

        ut = t.UnionType(*branch_types)
        if len(ut) == 1:
            type, *_ = ut
            return type

        return ut

    @visitor.when(ast.LetExprNode)
    def visit(self, node: ast.LetExprNode, ctx: Context, scope: Scope):
        vt = self.visit(node.value, ctx, scope)
        at = get_safe_type(node.type, ctx)

        child_scope = scope.create_child()
        child_scope.define_variable(node.id, at if at is not None else vt)

        return self.visit(node.body, ctx, child_scope)

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
    def visit(self, node: ast.ProgramNode, ctx: Context, scope: Scope) -> Type | Proto:
        pass


# PD: I AM COOKING HERE...
