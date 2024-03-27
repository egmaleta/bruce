from ..tools.semantic import SemanticError, Type
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from ..tools.graph import topological_order
from ..tools import visitor
from ..types import BOOLEAN_TYPE, NUMBER_TYPE
from ..ast import *


class TypeChecker:
    def __init__(self, errors=[]):
        self.current_type: Type = None
        self.current_method = None
        self.errors = errors

    @visitor.on("node")
    def visit(self, node, ctx: Context, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, ctx: Context, scope=None):
        scope = Scope()
        types_node = [
            member for member in node.declarations if isinstance(member, TypeNode)
        ]
        order = topological_order(types_node)
        if len(order) != len(types_node):
            self.errors.append("Circular inheritance")
        else:
            for declaration in order:
                self.visit(declaration, ctx, scope.create_child())
            self.visit(node.expr, ctx, scope.create_child())
        return scope

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context, scope: Scope):
        self.current_type: Type = get_safe_type(node.type, ctx)
        for param in node.params:
            scope.define_variable(param[0], get_safe_type(param[1], ctx))
        # This is to know if the args of the parents are ok
        if node.parent_type:
            if node.params:
                parent_type = get_safe_type(node.parent_type, ctx)
                parent_args_size = len(parent_type.params) if parent_type.params else 0
                node_parent_args_size = len(node.parent_args) if node.parent_args else 0
                if parent_args_size != node_parent_args_size:
                    self.errors.append(
                        f"Type {node.parent_type} expects {parent_args_size} arguments but {node_parent_args_size} were given"
                    )

                if parent_type.params and node.parent_args:
                    for parent_arg, node_arg in zip(
                        parent_type.params, node.parent_args
                    ):
                        arg_type = self.visit(node_arg, ctx, scope.create_child())
                        parent_arg_type = parent_type.params[parent_arg]
                        if not arg_type.conforms_to(parent_arg_type):
                            self.errors.append(
                                f"Cannot convert {arg_type.name} into {parent_arg.type.name}"
                            )
            else:
                parent_type = get_safe_type(node.parent_type, ctx)
                self.current_type.set_parent(parent_type.params)

        for member in node.members:
            if isinstance(member, TypePropertyNode):
                self.visit(member, ctx, scope.create_child())

        for member in node.members:
            if isinstance(member, FunctionNode):
                scope.define_variable("self", self.current_type)
                scope.define_variable("base", self.current_type.parent)
                self.visit(member, ctx, scope.create_child())

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        self.current_method = self.current_type.get_method(node.id)
        for param in node.params:
            self.visit(param, ctx, scope)
        body_type = self.visit(node.body, ctx, scope.create_child())
        return_type = get_safe_type(node.return_type, ctx)
        if not body_type.conforms_to(return_type):
            self.errors.append(f"Cannot convert {body_type.name} in {node.return_type}")

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        attributte_type = self.visit(node.value, ctx, scope.create_child())
        node_type = get_safe_type(node.type, ctx)
        if not attributte_type.conforms_to(node_type):
            self.errors.append(
                f"Cannot convert {attributte_type.name} to {node_type.name}"
            )

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, ctx: Context, scope: Scope):
        for member in node.exprs:
            self.visit(member, ctx, scope.create_child())

    @visitor.when(MemberAccessingNode)
    def visit(self, node: MemberAccessingNode, ctx: Context, scope: Scope):
        try:
            target = self.visit(node.target, ctx, scope.create_child())
            if not target:
                self.errors.append(f"Variable {node.target} not defined")
            else:
                try:
                    return target.get_method(node.member_id)
                except SemanticError as se:
                    if (
                        target == self.current_type
                        and isinstance(node.target, IdentifierNode)
                        and node.target.value == "self"
                    ):
                        return target.get_attribute(node.member_id).type
                    else:
                        self.errors.append(se.text)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(FunctionCallNode)
    def visit(self, node: FunctionCallNode, ctx: Context, scope: Scope):
        try:
            method = self.visit(node.target, ctx, scope.create_child())
            if not method:
                self.errors.append(f"Method {node.target} not defined")
            else:
                if len(node.args) != len(method.params):
                    self.errors.append(
                        f"Method {node.target} expects {len(method.params)} arguments but {len(node.args)} were given"
                    )
                else:
                    for arg, param in zip(node.args, method.params):
                        arg_type = self.visit(arg, ctx, scope.create_child())
                        if not arg_type.conforms_to(param.type):
                            self.errors.append(
                                f"Cannot convert {arg_type.name} to {param.type.name}"
                            )
            return method.type
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, ctx: Context, scope: Scope):
        # node.type = self.context.get_type("object").name if not node.type else node.type
        if scope.is_defined(node.id):
            self.errors.append(f"Variable {node.id} already defined")
        self.visit(node.value, ctx, scope.create_child())
        if node.type:
            node_type = self.context.get_type(node.type)
            if not self.current_type.conforms_to(node_type):
                self.errors.append(
                    f"Cannot convert {self.current_type.name} to {node_type.name}"
                )
        scope.define_variable(node.id, self.current_type)
        self.visit(node.body, ctx, scope.create_child())

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, ctx: Context, scope: Scope):
        # Check the size of args of the type and the instance
        current_type = get_safe_type(node.type, ctx)
        node_args_size = len(node.args) if node.args else 0
        type_args_size = len(current_type.params) if current_type.params else 0
        if type_args_size != node_args_size:
            self.errors.append(
                f"Type {node.type} expects {type_args_size} arguments, but {node_args_size} were given"
            )

        for arg in node.args:
            arg_type = self.visit(arg, ctx, scope.create_child())
            node_type = self.context.get_type(node.type)
            if not node_type.conforms_to(arg_type):
                self.errors.append(
                    f"Cannot convert {arg_type.name} to {node_type.name}"
                )
        return get_safe_type(node.type, ctx)

    @visitor.when(ArithOpNode)
    def visit(self, node: ArithOpNode, ctx: Context, scope: Scope):
        try:
            left = self.visit(node.left, ctx, scope.create_child())
            right = self.visit(node.right, ctx, scope.create_child())
            if left != NUMBER_TYPE or right != NUMBER_TYPE:
                self.errors.append(
                    f"Operation '{node.operator}' is not defined between {left.name} and {right.name}"
                )
        except SemanticError as se:
            self.errors.append(se.text)
        except AttributeError as ae:
            pass  # TODO Fix this when left or right return None
        return NUMBER_TYPE

    @visitor.when(BooleanNode)
    def visit(self, node: BooleanNode, ctx: Context, scope: Scope):
        self.current_type = BOOLEAN_TYPE

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, ctx: Context, scope: Scope):
        return scope.find_variable(node.value).type

    @visitor.when(NumberNode)
    def visit(self, node: NumberNode, ctx: Context, scope: Scope):
        return NUMBER_TYPE
