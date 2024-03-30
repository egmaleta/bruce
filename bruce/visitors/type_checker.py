from ..tools.semantic import Function, SemanticError, Type, allow_type
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from .type_builder import topological_order
from ..tools import visitor
from ..types import (
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

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context, scope: Scope):
        self.current_type: Type = get_safe_type(node.type, ctx)
        scope_params = scope.create_child()
        for param in node.params:
            scope_params.define_variable(param[0], get_safe_type(param[1], ctx))
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
                                f"Cannot convert {arg_type.name} into {parent_arg.type.name}"
                            )
            else:
                parent_type = get_safe_type(node.parent_type, ctx)
                self.current_type.set_parent(parent_type.params)

        for member in node.members:
            if isinstance(member, TypePropertyNode):
                self.visit(member, ctx, scope_params.create_child())

        if scope.is_var_defined("self"):
            self.errors.append("Cannot redefine self")
        else:
            scope.define_variable("self", self.current_type)
        for member in node.members:
            if isinstance(member, FunctionNode):
                self.visit(member, ctx, scope.create_child())

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        self.current_method = self.current_type.get_method(node.id)
        for param in node.params:
            self.visit(param, ctx, scope)
        body_type = self.visit(node.body, ctx, scope.create_child())
        return_type = get_safe_type(node.return_type, ctx)
        if not allow_type(body_type, return_type):
            self.errors.append(f"Cannot convert {body_type.name} in {node.return_type}")

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        attributte_type = self.visit(node.value, ctx, scope.create_child())
        node_type = get_safe_type(node.type, ctx)
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

    @visitor.when(MemberAccessingNode)
    def visit(self, node: MemberAccessingNode, ctx: Context, scope: Scope):
        try:
            target = self.visit(node.target, ctx, scope.create_child())
            if target == ERROR_TYPE:
                return target
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
                        and (
                            "self" not in [pn for pn in self.current_type.params.keys()]
                        )
                    ):
                        return target.get_attribute(node.member_id).type
                    else:
                        self.errors.append(se.text)
                    return ERROR_TYPE
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(FunctionCallNode)
    def visit(self, node: FunctionCallNode, ctx: Context, scope: Scope):
        try:
            # Case: id (...)
            if isinstance(node.target, IdentifierNode):
                method = self.visit(node.target, ctx, scope.create_child())
                if method is not Function:
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
            
            
            method = self.visit(node.target, ctx, scope.create_child())
            if method == ERROR_TYPE:
                return ERROR_TYPE
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
                        if not allow_type(arg_type, method.params[param]):
                            self.errors.append(
                                f"Cannot convert {arg_type.name} to {method.params[param].name}"
                            )
            return method.type
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, ctx: Context, scope: Scope):
        try:
            if scope.is_var_defined(node.id):
                self.errors.append(f"Variable {node.id} already defined")
            value_type = self.visit(node.value, ctx, scope.create_child())
            node_type = get_safe_type(node.type, ctx)
            if not allow_type(value_type, node_type):
                self.errors.append(
                    f"Cannot convert {value_type.name} to {node_type.name}"
                )
            scope.define_variable(node.id, node_type)
            return self.visit(node.body, ctx, scope.create_child())
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, ctx: Context, scope: Scope):
        try:
            target = self.visit(node.target, ctx, scope.create_child())
            if not target:
                self.errors.append(f"Variable {node.target} not defined")
            else:
                value_type = self.visit(node.value, ctx, scope.create_child())
                if not allow_type(value_type, target):
                    self.errors.append(
                        f"Cannot convert {value_type.name} to {target.type.name}"
                    )
                return value_type
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, ctx: Context, scope: Scope):
        try:
            instance_type = get_safe_type(node.type, ctx)
            if instance_type.params:
                if len(node.args) != len(instance_type.params):
                    self.errors.append(
                        f"Type {node.type} expects {len(type.params)} arguments but {len(node.args)} were given"
                    )
                else:
                    for arg, param in zip(node.args, instance_type.params):
                        arg_type = self.visit(arg, ctx, scope.create_child())
                        if not allow_type(arg_type, instance_type.params[param]):
                            self.errors.append(
                                f"Cannot convert {arg_type.name} to {param.name}"
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
        return NUMBER_TYPE

    @visitor.when(PowerOpNode)
    def visit(self, node: PowerOpNode, ctx: Context, scope: Scope):
        try:
            left = self.visit(node.left, ctx, scope.create_child())
            right = self.visit(node.right, ctx, scope.create_child())
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
            if left != NUMBER_TYPE or right != NUMBER_TYPE:
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
                    f"Type {iterable_type.name} does not implement Iterable"
                )
            scope_mapped = scope.create_child()
            scope_mapped.define(node.item_id, iterable_type)
            map_expr_type = self.visit(node.map_expr, ctx, scope_mapped)
            if not allow_type(map_expr_type, get_safe_type(node.item_type, ctx)):
                self.errors.append(
                    f"Cannot convert {map_expr_type.name} to {node.item_type}"
                )
            return VectorType(map_expr_type)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, ctx: Context, scope: Scope):
        try:
            types = [self.visit(expr, ctx, scope.create_child()) for expr in node.items]
            if len(set(types)) != 1:
                self.errors.append(f"Vector elements must have the same type")
            return VectorType(types[0])
        except SemanticError as se:
            self.errors.append(se.text)

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

    @visitor.when(DowncastingNode)
    def visit(self, node: DowncastingNode, ctx: Context, scope: Scope):
        try:
            target_type = self.visit(node.target, ctx, scope.create_child())
            if not allow_type(
                target_type, get_safe_type(node.type, ctx)
            ) and not allow_type(get_safe_type(node.type, ctx), target_type):
                self.errors.append(
                    f"Cannot cast {target_type.name} to {node.type.name}"
                )
            return get_safe_type(node.type, ctx)
        except SemanticError as se:
            self.errors.append(se.text)

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
