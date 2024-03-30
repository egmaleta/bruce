from typing import Union

from ..tools import visitor
from ..tools.semantic import Type, Proto, SemanticError, Method
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from .. import ast
from .. import types as t
from ..names import SIZE_METHOD_NAME, INSTANCE_NAME, CURRENT_METHOD_NAME


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
        if (
            self.current_method is not None
            and node.value == INSTANCE_NAME
            and node.value not in self.current_method.params
            and scope.find_variable(node.value).owner_scope.is_function_scope
        ):
            # 'self' refers to current type
            return self.current_type

        var = scope.find_variable(node.value)
        if var is not None:
            return var.type

        return t.FUNCTION_TYPE

    @visitor.when(ast.TypeInstancingNode)
    def visit(self, node: ast.TypeInstancingNode, ctx: Context, scope: Scope):
        for arg in node.args:
            self.visit(arg, ctx, scope)

        it = get_safe_type(node.type, ctx)
        for arg, pt in zip(node.args, it.params.values()):
            if pt is not None:
                self._infer(arg, scope, pt)

        return it

    @visitor.when(ast.VectorNode)
    def visit(self, node: ast.VectorNode, ctx: Context, scope: Scope):
        item_types = []
        for item in node.items:
            item_t = self.visit(item, ctx, scope)
            if item_t is not None:
                item_types.append(item_t)

        if len(item_types) > 0:
            ut = t.union_type(*item_types)
            for item in node.items:
                self._infer(item, scope, ut)

            return t.VectorType(ut)

        return t.VectorType(t.OBJECT_TYPE)

    @visitor.when(ast.MappedIterableNode)
    def visit(self, node: ast.MappedIterableNode, ctx: Context, scope: Scope):
        it = get_safe_type(node.item_type, ctx)
        iterable_t = self.visit(node.iterable_expr, ctx, scope)

        self._infer(node.iterable_expr, scope, t.ITERABLE_PROTO)

        if it is None:
            if isinstance(iterable_t, t.VectorType):
                it = iterable_t.item_type
            elif isinstance(iterable_t, Type) and iterable_t.implements(
                t.ITERABLE_PROTO
            ):
                it = iterable_t.get_method(CURRENT_METHOD_NAME).type
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
            self.current_method is not None
            and isinstance(node.target, ast.IdentifierNode)
            and node.target.value == INSTANCE_NAME
            and node.target.value not in self.current_method.params
            and scope.find_variable(node.target.value).owner_scope.is_function_scope
        ):
            # 'self' refers to current type
            try:
                return self.current_type.get_attribute(node.member_id).type
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
        if isinstance(node.target, ast.MemberAccessingNode):
            receiver = node.target.target
            member = node.target.member_id

            rt = self.visit(receiver, ctx, scope)
            for arg in node.args:
                self.visit(arg, ctx, scope)

            if rt is not None:
                try:
                    method = rt.get_method(member)
                except SemanticError:
                    pass
                else:
                    for arg, pt in zip(node.args, method.params.values()):
                        if pt is not None:
                            self._infer(arg, scope, pt)

                return rt
        else:
            tt = self.visit(node.target, ctx, scope)
            for arg in node.args:
                self.visit(arg, ctx, scope)

            if tt != t.FUNCTION_TYPE:
                return None

            if isinstance(node.target, ast.IdentifierNode):
                f = scope.find_function(node.target.value)
                if f is not None:
                    for arg, pt in zip(node.args, f.params.values()):
                        if pt is not None:
                            self._infer(arg, scope, pt)

                    return f.type

        return None

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
        self.visit(node.target, ctx, scope)

        vt = self.visit(node.value, ctx, scope)
        if vt is not None:
            self._infer(node.target, scope, vt)

        return vt

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

        self._infer(node.left, scope, t.NUMBER_TYPE)
        self._infer(node.right, scope, t.NUMBER_TYPE)

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

        ut = t.union_type(t.NUMBER_TYPE, t.STRING_TYPE)
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
        bt = self.visit(node.body, ctx, scope.create_child())
        ft = self.visit(node.fallback_expr, ctx, scope.create_child())

        self._infer(node.condition, scope, t.BOOLEAN_TYPE)

        if bt is None or ft is None:
            return None

        return t.union_type(bt, ft)

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, ctx: Context, scope: Scope):
        branch_types = []

        for cond, branch in node.condition_branchs:
            self.visit(cond, ctx, scope)

            bt = self.visit(branch, ctx, scope.create_child())
            branch_types.append(bt)

        ft = self.visit(node.fallback_branch, ctx, scope.create_child())
        branch_types.append(ft)

        for cond, _ in node.condition_branchs:
            self._infer(cond, scope, t.BOOLEAN_TYPE)

        if any(bt is None for bt in branch_types):
            return None

        return t.union_type(*branch_types)

    @visitor.when(ast.LetExprNode)
    def visit(self, node: ast.LetExprNode, ctx: Context, scope: Scope):
        vt = self.visit(node.value, ctx, scope)
        at = get_safe_type(node.type, ctx)

        child_scope = scope.create_child()
        child_scope.define_variable(node.id, at if at is not None else vt)

        return self.visit(node.body, ctx, child_scope)

    @visitor.when(ast.FunctionNode)
    def visit(self, node: ast.FunctionNode, ctx: Context, scope: Scope):
        is_method = self.current_method is not None

        f = self.current_method if is_method else scope.find_function(node.id)

        child_scope = scope.get_top_scope().create_child(is_function_scope=True)
        for name, pt in f.params.items():
            child_scope.define_variable(name, pt)

        if is_method and INSTANCE_NAME not in f.params:
            child_scope.define_variable(INSTANCE_NAME, self.current_type)

        rt = self.visit(node.body, ctx, child_scope)

        # infer function param types
        for name, pt in f.params.items():
            if pt is None:
                var = child_scope.find_variable(name)
                if var.type is not None:
                    f.set_param_type(name, var.type)

        if f.type is None and rt is not None:
            f.set_type(rt)
            self.occurs = True

    @visitor.when(ast.TypeNode)
    def visit(self, node: ast.TypeNode, ctx: Context, scope: Scope):
        type = get_safe_type(node.type, ctx)
        self.current_type = type

        child_scope = scope.create_child()
        for name, pt in type.params.items():
            child_scope.define_variable(name, pt)

        # infer attr types
        property_nodes = [
            node for node in node.members if isinstance(node, ast.TypePropertyNode)
        ]
        for attr, pn in zip(type.attributes, property_nodes):
            pnt = self.visit(pn.value, ctx, child_scope)
            if attr.type is None and pnt is not None:
                attr.set_type(pnt)
                self.occurs = True

        # infer type param types by attr init
        for name, pt in type.params.items():
            if pt is None:
                var = child_scope.find_variable(name)
                if var.type is not None:
                    type.set_param_type(name, var.type)

        if node.parent_args:
            child_scope = scope.create_child()
            for name, pt in type.params.items():
                child_scope.define_variable(name, pt)

            for arg in node.parent_args:
                self.visit(arg, ctx, child_scope)

            # infer type param types by parent type args
            for name, pt in type.params.items():
                if pt is None:
                    var = child_scope.find_variable(name)
                    if var.type is not None:
                        type.set_param_type(name, var.type)

        method_nodes = [
            node for node in node.members if isinstance(node, ast.FunctionNode)
        ]
        for method, mnode in zip(type.methods, method_nodes):
            self.current_method = method
            self.visit(mnode, ctx, scope)
            self.current_method = None

        self.current_type = None

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, ctx: Context, scope: Scope) -> Type | Proto:
        while True:
            self.occurs = False

            for decl in node.declarations:
                if not isinstance(decl, ast.ProtocolNode):
                    self.visit(decl, ctx, scope)

            if self.occurs == False:
                break

        for type in ctx.types.values():
            for name, ptype in type.params.items():
                if ptype is None:
                    self.errors.append(
                        f"Couldn't infer type of constructor param '{name}' of type '{type.name}'."
                    )

            for attr in type.attributes:
                if attr.type is None:
                    self.errors.append(
                        f"Couldn't infer type of attribute '{attr.name}' of type '{type.name}'."
                    )

            for method in type.methods:
                for name, ptype in method.params.items():
                    self.errors.append(
                        f"Couldn't infer type of param '{name}' of method '{type.name}.{method.name}'."
                    )

                if method.type is None:
                    self.errors.append(
                        f"Couldn't infer return type of method '{type.name}.{method.name}'."
                    )

        for f in scope.local_funcs.values():
            for name, type in f.params.items():
                if type is None:
                    self.errors.append(
                        f"Couldn't infer type of param '{name}' of function '{f.name}'."
                    )

            if f.type is None:
                self.errors.append(
                    f"Couldn't infer return type of function '{f.name}'."
                )
        
        return node
