from ..tools.semantic import Attribute, Function, SemanticError
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from ..tools import visitor
from .. import names
from ..ast import *


class SemanticChecker:
    @staticmethod
    def is_assignable(node: ASTNode):
        is_assignable_id = isinstance(node, IdentifierNode) and (not node.is_builtin)
        return is_assignable_id or isinstance(node, (IndexingNode, MemberAccessingNode))

    def __init__(self):
        self.errors: list[str] = []

    @visitor.on("node")
    def visit(self, node, ctx, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, ctx: Context, scope: Scope):
        for declaration in node.declarations:
            self.visit(declaration, ctx, scope)

        self.visit(node.expr, ctx, scope)

        return self.errors

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, ctx: Context, scope: Scope):
        if (
            # not node.value == "self"
            not scope.is_var_defined(node.value)
            and not scope.is_func_defined(node.value)
        ):
            self.errors.append(f"Variable {node.value} not defined")

    @visitor.when(FunctionCallNode)
    def visit(self, node: FunctionCallNode, ctx: Context, scope: Scope):
        self.visit(node.target, ctx, scope)

        for arg in node.args:
            self.visit(arg, ctx, scope)

        if isinstance(node.target, IdentifierNode):
            f = scope.find_function(node.target.value)
            if f is None:
                self.errors.append(f"Function {node.target.value} is not defined")
            else:
                if len(node.args) != len(f.params):
                    self.errors.append(
                        f"The number of arguments don't match the number of params of {f.name}"
                    )

        elif not (isinstance(node.target, MemberAccessingNode)):
            self.errors.append(
                f"Cannot call a Function with targets that ar not MemeberAccesing or Identifier"
            )

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        func_scope = scope.create_child(is_function_scope=True)
        for name, _ in node.params:
            func_scope.define_variable(name)

        self.visit(node.body, ctx, func_scope)

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, ctx: Context, scope: Scope):
        for expr in node.exprs:
            self.visit(expr, ctx, scope.create_child())

    @visitor.when(BinaryOpNode)
    def visit(self, node: BinaryOpNode, ctx: Context, scope: Scope):
        self.visit(node.left, ctx, scope)
        self.visit(node.right, ctx, scope)

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, ctx: Context, scope: Scope):
        self.visit(node.target, ctx, scope)
        self.visit(node.value, ctx, scope)

        if not self.is_assignable(node.target):
            self.errors.append(f"Expression '' does not support destructive assignment")

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, ctx: Context, scope: Scope):
        self.visit(node.value, ctx, scope)

        my_scope = scope.create_child()
        my_scope.define_variable(node.id)
        self.visit(node.body, ctx, my_scope)

    @visitor.when(ConditionalNode)
    def visit(self, node: ConditionalNode, ctx: Context, scope: Scope):
        for cond, body in node.condition_branchs:
            self.visit(cond, ctx, scope)
            self.visit(body, ctx, scope.create_child())

        self.visit(node.fallback_branch, ctx, scope.create_child())

    @visitor.when(LoopNode)
    def visit(self, node: LoopNode, ctx: Context, scope: Scope):
        self.visit(node.condition, ctx, scope)
        self.visit(node.body, ctx, scope.create_child())
        self.visit(node.fallback_expr, ctx, scope.create_child())

    @visitor.when(UnaryOpNode)
    def visit(self, node: UnaryOpNode, ctx: Context, scope: Scope):
        self.visit(node.operand, ctx, scope)

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context, scope: Scope):
        type = ctx.get_type(node.type)

        child_scope = scope.create_child()
        for name in type.params:
            child_scope.define_variable(name)

        for member in node.members:
            if isinstance(member, TypePropertyNode):
                self.visit(member.value, ctx, child_scope)

        if node.parent_args is not None:
            for expr in node.parent_args:
                self.visit(expr, ctx, child_scope)

        for member in node.members:
            if isinstance(member, FunctionNode):
                child_scope = scope.create_child(is_function_scope=True)

                method = type.get_method(member.id)
                for name in method.params:
                    child_scope.define_variable(name)

                if names.INSTANCE_NAME not in method.params:
                    child_scope.define_variable(names.INSTANCE_NAME)

                self.visit(member.body, ctx, child_scope)

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        self.visit(node.value, ctx, scope)

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, ctx: Context, scope: Scope):
        type = None

        try:
            type = ctx.get_type(node.type)
        except SemanticError:
            self.errors.append(
                f"Type {node.type} does not exist in the current context"
            )

        try:
            ctx.get_protocol(node.type)
        except:
            pass
        else:
            self.errors.append(
                f"Protocols, such as {node.type}, cannot be instantiated"
            )

        for arg in node.args:
            self.visit(arg, ctx, scope)

        if type is not None and len(node.args) != len(type.params):
            self.errors.append(
                f"The number of arguments don't match the number of params of {type.name}"
            )

    @visitor.when(TypeMatchingNode)
    def visit(self, node: TypeMatchingNode, ctx: Context, scope: Scope):
        try:
            ctx.get_type(node.type)
        except SemanticError:
            self.errors.append(
                f"Type {node.type} does not exist in the current context"
            )

        try:
            ctx.get_protocol(node.type)
        except SemanticError:
            self.errors.append(
                f"Protocol {node.type} does not exist in the current context"
            )

        self.visit(node.target, ctx, scope)

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, ctx: Context, scope: Scope):
        for expr in node.items:
            self.visit(expr, ctx, scope)

    @visitor.when(MappedIterableNode)
    def visit(self, node: MappedIterableNode, ctx: Context, scope: Scope):
        self.visit(node.iterable_expr, ctx, scope)

        my_scope = scope.create_child()
        my_scope.define_variable(node.item_id)
        self.visit(node.map_expr, ctx, my_scope)

    @visitor.when(MemberAccessingNode)
    def visit(self, node: MemberAccessingNode, ctx: Context, scope: Scope):
        self.visit(node.target, ctx, scope)

    @visitor.when(DowncastingNode)
    def visit(self, node: DowncastingNode, ctx: Context, scope: Scope):
        try:
            ctx.get_type(node.type)
        except SemanticError:
            self.errors.append(
                f"Type {node.type} does not exist in the current context"
            )

        try:
            ctx.get_protocol(node.type)
        except SemanticError:
            self.errors.append(
                f"Protocol {node.type} does not exist in the current context"
            )

        self.visit(node.target, ctx, scope)

    @visitor.when(MethodSpecNode)
    def visit(self, node: MethodSpecNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ProtocolNode)
    def visit(self, node: ProtocolNode, ctx: Context, scope: Scope):
        pass
