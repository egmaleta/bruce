from bruce import names
from ..tools.semantic import Function, SemanticError, Type
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from .type_builder import topological_order
from ..tools import visitor
from ..types import (
    allow_type,
    BOOLEAN_TYPE,
    ITERABLE_PROTO,
    NUMBER_TYPE,
    OBJECT_TYPE,
    STRING_TYPE,
    ERROR_TYPE,
    UnionType,
    VectorType,
)
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
    def visit(self, node: ProgramNode, ctx: Context, scope):
        for declaration in node.declarations:
            if isinstance(declaration, TypeNode):
                self.visit(declaration, ctx, scope.create_child())
        self.current_type = None
        self.visit(node.expr, ctx, scope.create_child())

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context, scope: Scope):
        self.current_type: Type = get_safe_type(node.type, ctx)
        scope_params = scope.get_top_scope().create_child()
        for n, t in self.current_type.params.items():
            scope_params.define_variable(n, t)
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
                        arg_type = self.visit(
                            node_arg, ctx, scope_params.create_child()
                        )
                        parent_arg_type = parent_type.params[parent_arg]
                        if not allow_type(arg_type, parent_arg_type):
                            self.errors.append(
                                f"Cannot convert {arg_type.name} into {parent_arg_type.name}"
                            )

        for member in node.members:
            if isinstance(member, TypePropertyNode):
                self.visit(member, ctx, scope_params.create_child())

        global_scope = scope.get_top_scope()
        for member in node.members:
            if isinstance(member, FunctionNode):
                child_scope = global_scope.create_child()
                child_scope.define_variable(names.INSTANCE_NAME, self.current_type)
                self.visit(member, ctx, child_scope)
                self.current_method = None

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        self.current_method = self.current_type.get_method(node.id)
        child_scope = scope.create_child()
        for param in self.current_method.params:
            child_scope.define_variable(param, self.current_method.params[param])
        body_type = self.visit(node.body, ctx, child_scope)
        if not allow_type(body_type, self.current_method.type):
            self.errors.append(
                f"Cannot convert {body_type.name} in {self.current_method.type.name}"
            )

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        attributte_type = self.visit(node.value, ctx, scope.create_child())
        node_type = self.current_type.get_attribute(node.id).type
        if not allow_type(attributte_type, node_type):
            self.errors.append(
                f"Cannot convert {attributte_type.name} to {node_type.name}"
            )

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, ctx: Context, scope: Scope):
        try:
            types = [self.visit(expr, ctx, scope.create_child()) for expr in node.exprs]
            return types[-1]
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(MemberAccessingNode)
    def visit(self, node: MemberAccessingNode, ctx: Context, scope: Scope):
        try:
            # Case: id

            if isinstance(node.target, IdentifierNode):
                target_var = scope.find_variable(node.target.value)
                if (
                    node.target.value == names.INSTANCE_NAME
                    and self.current_type is not None
                    and target_var is not None
                    and self.current_type == target_var.type
                    and names.INSTANCE_NAME not in self.current_method.params
                ):
                    att = self.current_type.get_attribute(node.member_id)
                    if att is None:
                        self.errors.append(
                            f"Attribute {node.member_id} does not exist in type {self.current_type}"
                        )
                    else:
                        return att.type
            self.errors.append(f"Cannot access attribute {node.member_id}")
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(FunctionCallNode)
    def visit(self, node: FunctionCallNode, ctx: Context, scope: Scope):
        try:
            # Case: id (...)

            if isinstance(node.target, IdentifierNode):

                # Case: base (...)

                if node.target.value == "base":
                    if self.current_method is None and self.current_type is None:
                        self.errors.append(
                            f"base() only can be invoked in a method of a class"
                        )
                        return ERROR_TYPE
                    elif self.current_type.parent is None:
                        self.errors.append(
                            f"{self.current_type.name} has no parent class and 'base()' cannot be called"
                        )
                        return ERROR_TYPE
                    else:
                        method = self.current_type.parent.get_method(
                            self.current_method.name
                        )
                        if method is None:
                            self.errors.append(
                                f"Method {self.current_method.name} not defined in type {self.current_type.parent.name}"
                            )
                            return ERROR_TYPE
                        if len(node.args) != len(method.params):
                            self.errors.append(
                                f"Method {self.current_method.name} expects {len(method.params)} arguments but {len(node.args)} were given"
                            )
                            return ERROR_TYPE
                        for arg, param in zip(node.args, method.params):
                            arg_type = self.visit(arg, ctx, scope.create_child())
                            if not allow_type(arg_type, method.params[param]):
                                self.errors.append(
                                    f"Cannot convert {arg_type.name} to {method.params[param].name}"
                                )
                                return ERROR_TYPE
                        return method.type
                method = self.visit(node.target, ctx, scope.create_child())
                if not isinstance(method, Function):
                    self.errors.append(f'Cannot invoke type "{method.name}"')
                    return ERROR_TYPE
                else:
                    if len(node.args) != len(method.params):
                        self.errors.append(
                            f"Method {node.target} expects {len(method.params)} arguments but {len(node.args)} were given"
                        )
                    else:
                        for arg, param in zip(node.args, method.params):
                            arg_type = self.visit(arg, ctx, scope.create_child())
                            if not allow_type(arg_type, method.params[param]):
                                self.errors.append(
                                    f"Cannot convert {arg_type.name} to {method.params[param].name}"
                                )
                    return method.type

            # Case: expr . id (...)

            expr = self.visit(node.target.target, ctx, scope.create_child())
            if expr == ERROR_TYPE:
                return ERROR_TYPE
            method = expr.get_method(node.target.member_id)
            if method is None:
                self.errors.append(
                    f"Method {node.target} not defined in type {expr.name}"
                )
            else:
                if len(node.args) != len(method.params):
                    self.errors.append(
                        f"Method {node.target.member_id} expects {len(method.params)} arguments but {len(node.args)} were given"
                    )
                else:
                    for arg, param in zip(node.args, method.params):
                        arg_type = self.visit(arg, ctx, scope.create_child())
                        if not allow_type(arg_type, method.params[param]):
                            self.errors.append(
                                f"Cannot convert {arg_type.name} to {method.params[param].name}"
                            )
            return method.type
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, ctx: Context, scope: Scope):
        try:
            value_type = self.visit(node.value, ctx, scope)
            node_type = (
                get_safe_type(node.type, ctx)
                if isinstance(node.type, str)
                else node.type
            )
            if not allow_type(value_type, node_type):
                self.errors.append(
                    f"Cannot convert {value_type.name} to {node_type.name}"
                )
            child_scope = scope.create_child()
            child_scope.define_variable(node.id, node_type)
            return self.visit(node.body, ctx, child_scope)
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, ctx: Context, scope: Scope):
        if isinstance(node.target, IdentifierNode) and node.target.value == "self":
            self.errors.append(f"self is not a valid assignment target")
            return ERROR_TYPE
        try:
            target = self.visit(node.target, ctx, scope.create_child())
            if not target:
                self.errors.append(f"Variable {node.target} not defined")
            else:
                value_type = self.visit(node.value, ctx, scope.create_child())
                if not allow_type(value_type, target):
                    self.errors.append(
                        f"Cannot convert {value_type.name} to {target.name}"
                    )
                return value_type
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, ctx: Context, scope: Scope):
        try:
            instance_type = get_safe_type(node.type, ctx)
            if instance_type.params:
                if len(node.args) != len(instance_type.params):
                    self.errors.append(
                        f"Type {node.type} expects {len(instance_type.params)} arguments but {len(node.args)} were given"
                    )
                else:
                    for arg, param in zip(node.args, instance_type.params):
                        arg_type = self.visit(arg, ctx, scope.create_child())
                        if not allow_type(arg_type, instance_type.params[param]):
                            self.errors.append(
                                f"Cannot convert {arg_type.name} to {instance_type.params[param].name}"
                            )
        except SemanticError as se:
            self.errors.append(se.text)
        return get_safe_type(node.type, ctx)

    @visitor.when(ConditionalNode)
    def visit(self, node: ConditionalNode, ctx: Context, scope: Scope):
        try:
            for cond, expr in node.condition_branchs:
                cond_type = self.visit(cond, ctx, scope.create_child())
                if cond_type != BOOLEAN_TYPE:
                    self.errors.append(
                        f"Condition must be boolean, not {cond_type.name}"
                    )
            types = [
                self.visit(expr, ctx, scope) for cond, expr in node.condition_branchs
            ]
            types += [self.visit(node.fallback_branch, ctx, scope)]
            return UnionType(*types)
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(LoopNode)
    def visit(self, node: LoopNode, ctx: Context, scope: Scope):
        try:
            cond_type = self.visit(node.condition, ctx, scope.create_child())
            if cond_type != BOOLEAN_TYPE:
                self.errors.append(f"Condition must be boolean, not {cond_type.name}")
            types = [self.visit(node.body, ctx, scope)]
            types += [self.visit(node.fallback_expr, ctx, scope)]
            return UnionType(*types)
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(ArithOpNode)
    def visit(self, node: ArithOpNode, ctx: Context, scope: Scope):
        try:
            left = self.visit(node.left, ctx, scope.create_child())
            right = self.visit(node.right, ctx, scope.create_child())
            if left == ERROR_TYPE or right == ERROR_TYPE:
                return NUMBER_TYPE
            if left != NUMBER_TYPE or right != NUMBER_TYPE:
                self.errors.append(
                    f"Operation '{node.operator}' is not defined between {left.name} and {right.name}"
                )
        except SemanticError as se:
            self.errors.append(se.text)
        return NUMBER_TYPE

    @visitor.when(PowerOpNode)
    def visit(self, node: PowerOpNode, ctx: Context, scope: Scope):
        try:
            left = self.visit(node.left, ctx, scope.create_child())
            right = self.visit(node.right, ctx, scope.create_child())
            if left == ERROR_TYPE or right == ERROR_TYPE:
                return NUMBER_TYPE
            if left != NUMBER_TYPE or right != NUMBER_TYPE:
                self.errors.append(
                    f"Operation '{node.operator}' is not defined between {left.name} and {right.name}"
                )
        except SemanticError as se:
            self.errors.append(se.text)
        return NUMBER_TYPE

    @visitor.when(ComparisonOpNode)
    def visit(self, node: ComparisonOpNode, ctx: Context, scope: Scope):
        try:
            left = self.visit(node.left, ctx, scope.create_child())
            right = self.visit(node.right, ctx, scope.create_child())
            if left == ERROR_TYPE or right == ERROR_TYPE:
                return BOOLEAN_TYPE
            if left != right:  # TODO right op
                self.errors.append(
                    f"Operation '{node.operator}' is not defined between {left.name} and {right.name}"
                )
        except SemanticError as se:
            self.errors.append(se.text)
        return BOOLEAN_TYPE

    @visitor.when(ConcatOpNode)
    def visit(self, node: ConcatOpNode, ctx: Context, scope: Scope):
        try:
            left = self.visit(node.left, ctx, scope.create_child())
            right = self.visit(node.right, ctx, scope.create_child())
            if left == ERROR_TYPE or right == ERROR_TYPE:
                return STRING_TYPE
            if (
                left != STRING_TYPE
                and left != NUMBER_TYPE
                or right != STRING_TYPE
                and right != NUMBER_TYPE
            ):
                self.errors.append(
                    f"Operation '{node.operator}' is not defined between {left.name} and {right.name}"
                )
        except SemanticError as se:
            self.errors.append(se.text)
        return STRING_TYPE

    @visitor.when(LogicOpNode)
    def visit(self, node: LogicOpNode, ctx: Context, scope: Scope):
        try:
            left = self.visit(node.left, ctx, scope.create_child())
            right = self.visit(node.right, ctx, scope.create_child())
            if left == ERROR_TYPE or right == ERROR_TYPE:
                return BOOLEAN_TYPE
            if left != BOOLEAN_TYPE or right != BOOLEAN_TYPE:
                self.errors.append(
                    f"Operation '{node.operator}' is not defined between {left.name} and {right.name}"
                )
        except SemanticError as se:
            self.errors.append(se.text)
        return BOOLEAN_TYPE

    @visitor.when(ArithNegOpNode)
    def visit(self, node: ArithNegOpNode, ctx: Context, scope: Scope):
        try:
            value = self.visit(node.value, ctx, scope.create_child())
            if value == ERROR_TYPE:
                return NUMBER_TYPE
            if value != NUMBER_TYPE:
                self.errors.append(
                    f"Operation '{node.operator}' is not defined for {value.name}"
                )
        except SemanticError as se:
            self.errors.append(se.text)
        return NUMBER_TYPE

    @visitor.when(NegOpNode)
    def visit(self, node: NegOpNode, ctx: Context, scope: Scope):
        try:
            value = self.visit(node.operand, ctx, scope.create_child())
            if value == ERROR_TYPE:
                return BOOLEAN_TYPE
            if value != BOOLEAN_TYPE:
                self.errors.append(f"Cannot negate a non-boolean value")
        except SemanticError as se:
            self.errors.append(se.text)
        return BOOLEAN_TYPE

    @visitor.when(MappedIterableNode)
    def visit(self, node: MappedIterableNode, ctx: Context, scope: Scope):
        try:
            iterable_type = self.visit(node.iterable_expr, ctx, scope.create_child())
            if iterable_type == ERROR_TYPE:
                return ERROR_TYPE
            if not iterable_type.implements(ITERABLE_PROTO):
                self.errors.append(
                    f"Type {iterable_type.name} does not implement Iterable protocol"
                )
            scope_mapped = scope.create_child()
            node_type = (
                get_safe_type(node.item_type)
                if isinstance(node.item_type, str)
                else node.item_type
            )
            scope_mapped.define_variable(node.item_id, node.item_type)
            map_expr_type = self.visit(node.map_expr, ctx, scope_mapped)
            if not allow_type(map_expr_type, node_type):
                self.errors.append(
                    f"Cannot convert {map_expr_type.name} to {node_type.name}"
                )
            return VectorType(map_expr_type)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, ctx: Context, scope: Scope):
        try:
            types = [self.visit(expr, ctx, scope) for expr in node.items]
            if len(set(types)) > 1:
                self.errors.append(f"Vector elements must have the same type")
            return VectorType(types[0]) if len(types) > 0 else VectorType(ERROR_TYPE)
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(TypeMatchingNode)
    def visit(self, node: TypeMatchingNode, ctx: Context, scope: Scope):
        try:
            target_type = self.visit(node.target, ctx, scope.create_child())
            if not allow_type(
                target_type, get_safe_type(node.type, ctx)
            ) and not allow_type(get_safe_type(node.type, ctx), target_type):
                self.errors.append(
                    f"Cannot convert {target_type.name} to {node.type.name}"
                )
            return BOOLEAN_TYPE
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(DowncastingNode)
    def visit(self, node: DowncastingNode, ctx: Context, scope: Scope):
        try:
            target_type = self.visit(node.target, ctx, scope.create_child())
            if not allow_type(
                target_type, get_safe_type(node.type, ctx)
            ) and not allow_type(get_safe_type(node.type, ctx), target_type):
                self.errors.append(f"Cannot cast {target_type.name} to {node.type}")
            return get_safe_type(node.type, ctx)
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(IndexingNode)
    def visit(self, node: IndexingNode, ctx: Context, scope: Scope):
        try:
            vector_type = self.visit(node.target, ctx, scope.create_child())
            if not isinstance(vector_type, VectorType):
                self.errors.append(f"Type {vector_type.name} does not support indexing")
            index_type = self.visit(node.index, ctx, scope.create_child())
            if index_type != NUMBER_TYPE:
                self.errors.append(f"Index must be a number, not {index_type.name}")
        except SemanticError as se:
            self.errors.append(se.text)
        return ERROR_TYPE

    @visitor.when(BooleanNode)
    def visit(self, node: BooleanNode, ctx: Context, scope: Scope):
        return BOOLEAN_TYPE

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, ctx: Context, scope: Scope):
        try:
            return scope.find_variable(node.value).type
        except AttributeError as ae:
            return scope.find_function(node.value)

    @visitor.when(NumberNode)
    def visit(self, node: NumberNode, ctx: Context, scope: Scope):
        return NUMBER_TYPE

    @visitor.when(StringNode)
    def visit(self, node: StringNode, ctx: Context, scope: Scope):
        return STRING_TYPE
