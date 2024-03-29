from ..tools.semantic.scope import Scope
from ..tools import visitor
from ..ast import *

from ..tools.semantic import SemanticError
from ..tools.semantic.context import Context


class SemanticChecker(object):  # TODO implement all the nodes
    def __init__(self):
        self.errors = []

    @visitor.on("node")
    def visit(self, node, ctx: Context, scope: Scope):
        pass

    @visitor.when(
        ProgramNode
    )  # falta ver que no esten def cosas con el mismo nombre y eso
    def visit(self, node: ProgramNode, ctx: Context, scope: Scope):
        program_scope = scope.create_child()
        for declaration in node.declarations:
            self.visit(declaration, ctx, program_scope)
        self.visit(node.expr, ctx, program_scope)

        return self.errors

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, ctx: Context, scope: Scope):

        if node.value != "self" and not scope.is_var_defined(node.value):
            self.errors.append(f"Variable {node.value} not defined")

    @visitor.when(FunctionCallNode)
    def visit(self, node: FunctionCallNode, ctx: Context, scope: Scope):
        my_scope = scope.get_top_scope().create_child(is_function_scope=True)
        for p in node.args:
            self.visit(p,ctx,my_scope)

        self.visit(node.target, ctx, my_scope)
        if not (
            isinstance(node.target, MemberAccessingNode)
            or isinstance(node.target, IdentifierNode)
        ):
            self.errors.append(
                f"Cannot call a Function with targets that ar not MemeberAccesing or Identifier"
            )

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        if not scope.is_func_defined(node.id):
            scope.define_function(node.id, node.params)
        else:
            self.errors.append(
                f"Function {node.id} alredy defined. Cannot define more than one function with the same name"
            )

        func_scope = scope.create_child()

        for param in node.params:
            func_scope.define_variable(param[0])

        # body es un BlockNode o  una expresion
        self.visit(node.body, ctx, func_scope)

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()
        for expr in node.exprs:
            self.visit(expr, ctx, my_scope)

    @visitor.when(BinaryOpNode)
    def visit(self, node: BinaryOpNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()
        self.visit(node.left, ctx, my_scope)
        self.visit(node.right, ctx, my_scope)

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()
        self.visit(node.target, ctx, my_scope)
        self.visit(node.value, ctx, my_scope)

        if not is_assignable(node.target):
            self.errors.append(f"Expression '' does not support destructive assignment")

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()
        my_scope.define_variable(node.id)
        self.visit(node.value, ctx, my_scope)
        self.visit(node.body, ctx, my_scope)

    @visitor.when(ConditionalNode)
    def visit(self, node: ConditionalNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()

        for branch in node.condition_branchs:
            self.visit(branch[0], ctx, my_scope)
            self.visit(branch[1], ctx, my_scope)

        self.visit(node.fallback_branch, ctx, my_scope)

    @visitor.when(LoopNode)
    def visit(self, node: LoopNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()

        self.visit(node.condition, ctx, my_scope)
        self.visit(node.body, ctx, my_scope)
        self.visit(node.fallback_expr, ctx, my_scope)

    @visitor.when(UnaryOpNode)
    def visit(self, node: UnaryOpNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()
        self.visit(node.operand, ctx, my_scope)

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()

        if node.params is not None:
            for param in node.params:
                my_scope.define_variable(param[0])

        if node.parent_args is not None:
            for expr in node.parent_args:
                self.visit(expr, ctx, my_scope)

        for member in node.members:
            self.visit(member, ctx, my_scope)

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()

        self.visit(node.value, ctx, my_scope)

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, ctx: Context, scope: Scope):
        try:
            ctx.get_type(node.type)
        except SemanticError:
            self.errors.append(
                f"Type {node.type} does not exist in the current context"
            )

        my_scope = scope.create_child()

        for arg in node.args:
            self.visit(arg, ctx, my_scope)

    @visitor.when(TypeMatchingNode)
    def visit(self, node: TypeMatchingNode, ctx: Context, scope: Scope):
        try:
            ctx.get_type(node.type)
        except SemanticError:
            self.errors.append(
                f"Type {node.type} does not exist in the current context"
            )
        my_scope = scope.create_child()
        self.visit(node.target, ctx, my_scope)

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()
        for expr in node.items:
            self.visit(expr, ctx, my_scope)

    @visitor.when(MappedIterableNode)
    def visit(self, node: MappedIterableNode, ctx: Context, scope: Scope):
        self.visit(ExprNode, ctx, scope)

        my_scope = scope.create_child()
        my_scope.define_variable(node.item_id)
        self.visit(node.map_expr, ctx, my_scope)

    @visitor.when(MemberAccessingNode)
    def visit(self, node: MemberAccessingNode, ctx: Context, scope: Scope):
        my_scope = scope.create_child()

        self.visit(node.target, ctx, my_scope)

    @visitor.when(DowncastingNode)
    def visit(self, node: DowncastingNode, ctx: Context, scope: Scope):
        try:
            ctx.get_type(node.type)
        except SemanticError:
            self.errors.append(
                f"Type {node.type} does not exist in the current context"
            )
        my_scope = scope.create_child()
        self.visit(node.target, ctx, my_scope)

    @visitor.when(MethodSpecNode)
    def visit(self, node: MethodSpecNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ProtocolNode)
    def visit(self, node: ProtocolNode, ctx: Context, scope: Scope):
        pass
