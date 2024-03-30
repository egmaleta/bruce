from math import sqrt, exp, log, sin, cos
from random import random

from ..tools import visitor
from ..tools.semantic import Type, Method, Proto, allow_type, Attribute
from ..types import (
    NUMBER_TYPE,
    STRING_TYPE,
    OBJECT_TYPE,
    BOOLEAN_TYPE,
    FUNCTION_TYPE,
    VectorTypeInstance,
    VectorType,
)
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from ..ast import *
from .. import names


def hulk_print(obj):
    print(obj[0])
    return obj


def hulk_range(min, max):
    min, max = min[0], max[0]

    if max <= min:
        raise ValueError(f"Range error: 'max' value must be greater than 'min' value.")

    return (
        VectorTypeInstance(NUMBER_TYPE, [(n, NUMBER_TYPE) for n in range(min, max)]),
        VectorType(NUMBER_TYPE),
    )


def hulk_sqrt(value):
    value = value[0]
    return (sqrt(value), NUMBER_TYPE)


def hulk_exp(value):
    value = value[0]
    return (exp(value), NUMBER_TYPE)


def hulk_log(base, value):
    base, value = base[0], value[0]
    return (log(value, base), NUMBER_TYPE)


def hulk_rand(*_):
    return (random(), NUMBER_TYPE)


def hulk_sin(angle):
    angle = angle[0]
    return (sin(angle), NUMBER_TYPE)


def hulk_cos(angle):
    angle = angle[0]
    return (cos(angle), NUMBER_TYPE)


class Evaluator:
    artih_op_funcs = {
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y,
        "%": lambda x, y: x % y,
    }

    comparison_funcs = {
        ">": lambda x, y: x > y,
        "<": lambda x, y: x < y,
        "<=": lambda x, y: x <= y,
        ">=": lambda x, y: x >= y,
        "==": lambda x, y: x == y,
        "!=": lambda x, y: x != y,
    }

    logic_funcs = {
        "&": lambda x, y: x and y,
        "|": lambda x, y: x or y,
    }

    builtin_funcs = {
        names.PRINT_FUNC_NAME: hulk_print,
        names.RANGE_FUNC_NAME: hulk_range,
        names.SQRT_FUNC_NAME: hulk_sqrt,
        names.EXP_FUNC_NAME: hulk_exp,
        names.LOG_FUNC_NAME: hulk_log,
        names.RAND_FUNC_NAME: hulk_rand,
        names.SIN_FUNC_NAME: hulk_sin,
        names.COS_FUNC_NAME: hulk_cos,
    }

    def __init__(self, errors=[]) -> None:
        self.errors = errors

        self.current_type: Type = None
        self.current_method: Method = None

    @visitor.on("node")
    def visit(self, node, context: Context, scope: Scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, ctx: Context, scope: Scope):
        # seed function bodies and type attrs
        for decl in node.declarations:
            if not isinstance(decl, ProtocolNode):
                self.visit(decl, ctx, scope)

        return self.visit(node.expr, ctx, scope)[0]

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context, scope: Scope):
        self.current_type = ctx.get_type(node.type)

        for member in node.members:
            if isinstance(member, TypePropertyNode):
                self.visit(member, ctx, scope)
            else:
                self.current_method = scope.find_function(member.id)
                self.visit(member, ctx, scope)
                self.current_method = None

        if node.parent_args:
            self.current_type.set_parent_args(node.parent_args)

        self.current_type = None

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        is_method = self.current_method is not None

        if is_method:
            self.current_method.set_body(node.body)
        else:
            f = scope.find_function(node.id)
            f.set_body(node.body)

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        attr = self.current_type.get_attribute(node.id)
        attr.set_init_expr(node.value)

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, ctx: Context, scope: Scope):
        value, value_type = None, None
        for expr in node.exprs:
            value, value_type = self.visit(expr, ctx, scope.create_child())
        return value, value_type

    @visitor.when(MemberAccessingNode)
    def visit(self, node: MemberAccessingNode, ctx: Context, scope: Scope):
        # evaluates only attribute accessing
        # method handling is done in FunctionCall visitor
        assert isinstance(node.target, IdentifierNode)
        assert node.target.value == names.INSTANCE_NAME

        receiver, _ = self.visit(node.target, ctx, scope)
        assert isinstance(receiver, Type)

        attr = receiver.get_attribute(node.member_id)
        assert isinstance(attr, Attribute)

        return attr.value

    @visitor.when(FunctionCallNode)
    def visit(self, node: FunctionCallNode, ctx: Context, scope: Scope):
        if isinstance(node.target, IdentifierNode):
            # handle builtin funcs
            if node.target.is_builtin:
                f = self.builtin_funcs[node.target.value]
                arg_values = [self.visit(arg, ctx, scope) for arg in node.args]
                return f(*arg_values)

            f, _ = self.visit(node.target, ctx, scope)
            arg_values = [self.visit(arg, ctx, scope) for arg in node.args]

            top_scope = scope.get_top_scope()
            child_scope = top_scope.create_child(is_function_scope=True)
            for name, value in zip(f.params, arg_values):
                child_scope.define_variable(name, None, value)

            return self.visit(f.body, ctx, child_scope)

        assert isinstance(node.target, MemberAccessingNode)
        target = node.target.target
        method_name = node.target.member_id

        inst, inst_type = self.visit(target, ctx, scope)
        method = inst.get_method(method_name)

        arg_values = [self.visit(arg, ctx, scope) for arg in node.args]

        top_scope = scope.get_top_scope()
        child_scope = top_scope.create_child(is_function_scope=True)
        for name, value in zip(method.params, arg_values):
            child_scope.define_variable(name, None, value)

        if names.INSTANCE_NAME not in method.params:
            child_scope.define_variable(names.INSTANCE_NAME, None, (inst, inst_type))

        return self.visit(method.body, ctx, child_scope)

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, ctx: Context, scope: Scope):
        child = scope.create_child()
        value, value_type = self.visit(node.value, ctx, child)
        child.define_variable(node.id, node.type, (value, value_type))
        return self.visit(node.body, ctx, child)

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, ctx: Context, scope: Scope):
        value, value_type = self.visit(node.value, ctx, scope.create_child())
        if isinstance(node.target, IdentifierNode):
            scope.find_variable(node.target.value).set_value((value, value_type))
        elif isinstance(node.target, MemberAccessingNode):
            target = node.target.target
            inst, inst_type = self.visit(target, ctx, scope)
            attr = inst.get_attribute(node.target.member_id)
            attr.set_value((value, value_type))

        return value, value_type

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, ctx: Context, scope: Scope):
        global_scope = scope.get_top_scope()

        dyn_type = ctx.get_type(node.type)

        arg_values = [self.visit(arg, ctx, scope) for arg in node.args]
        instance = dyn_type.clone()

        while True:
            child_scope = global_scope.create_child()

            for name, value in zip(instance.params, arg_values):
                child_scope.define_variable(name, None, value)

            # init instance attrs
            for attr in instance.attributes:
                attr.set_value(self.visit(attr.init_expr, ctx, child_scope))

            if instance.parent == OBJECT_TYPE:
                break

            parent_args = (
                instance.parent_args
                if instance.parent_args is not None
                else [IdentifierNode(name) for name in instance.params]
            )

            arg_values = [self.visit(arg, ctx, child_scope) for arg in parent_args]
            instance = instance.parent

        return (instance, dyn_type)

    @visitor.when(ConditionalNode)
    def visit(self, node: ConditionalNode, ctx: Context, scope: Scope):
        for cond, expr in node.condition_branchs:
            value, value_type = self.visit(cond, ctx, scope.create_child())
            if value:
                return self.visit(expr, ctx, scope.create_child())
        return self.visit(node.fallback_branch, ctx, scope.create_child())

    @visitor.when(LoopNode)
    def visit(self, node: LoopNode, ctx: Context, scope: Scope):
        condition, condition_type = self.visit(
            node.condition, ctx, scope.create_child()
        )
        if not condition:
            fb_expr, fb_type = self.visit(node.fallback_expr, ctx, scope.create_child())
            return fb_expr, fb_type
        else:
            while condition:
                body, body_type = self.visit(node.body, ctx, scope.create_child())
                condition, condition_type = self.visit(
                    node.condition, ctx, scope.create_child()
                )
            return body, body_type

    @visitor.when(ArithOpNode)
    def visit(self, node: ArithOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)
        return (
            Evaluator.artih_op_funcs[node.operator](left_value, right_value),
            NUMBER_TYPE,
        )

    @visitor.when(PowerOpNode)
    def visit(self, node: PowerOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)
        return left_value**right_value, NUMBER_TYPE

    @visitor.when(ComparisonOpNode)
    def visit(self, node: ComparisonOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)
        return (
            Evaluator.comparison_funcs[node.operator](left_value, right_value),
            BOOLEAN_TYPE,
        )

    @visitor.when(ConcatOpNode)
    def visit(self, node: ConcatOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)

        return str(left_value) + str(right_value), STRING_TYPE

    @visitor.when(LogicOpNode)
    def visit(self, node: LogicOpNode, ctx: Context, scope: Scope):

        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)

        return (
            Evaluator.logic_funcs[node.operator](left_value, right_value),
            BOOLEAN_TYPE,
        )

    @visitor.when(ArithNegOpNode)
    def visit(self, node: ArithNegOpNode, ctx: Context, scope: Scope):
        value, node_type = self.visit(node.operand, ctx, scope)
        return (-value), NUMBER_TYPE

    @visitor.when(NegOpNode)
    def visit(self, node: NegOpNode, ctx: Context, scope: Scope):
        value, node_type = self.visit(node.operand, ctx, scope)
        return not value, node_type

    @visitor.when(MappedIterableNode)
    def visit(self, node: MappedIterableNode, ctx: Context, scope: Scope):
        iterable, iterable_type = self.visit(node.iterable_expr, ctx, scope)
        assert isinstance(iterable, VectorTypeInstance)

        tuples = []

        top_scope = scope.get_top_scope()

        while True:
            child_scope = top_scope.create_child(is_function_scope=True)
            child_scope.define_variable(names.INSTANCE_NAME, iterable)
            cond, _ = self.visit(
                iterable.get_method(names.NEXT_METHOD_NAME).body, ctx, child_scope
            )

            if not cond:
                break

            child_scope = top_scope.create_child(is_function_scope=True)
            child_scope.define_variable(names.INSTANCE_NAME, iterable)
            item_value = self.visit(
                iterable.get_method(names.CURRENT_METHOD_NAME).body,
                ctx,
                child_scope,
            )

            child_scope = scope.create_child()
            child_scope.define_variable(node.item_id, None, item_value)
            value = self.visit(node.map_expr, ctx, child_scope)
            tuples.append(value)

        return (VectorTypeInstance(OBJECT_TYPE, tuples), VectorType(OBJECT_TYPE))

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, ctx: Context, scope: Scope):
        tuples = [self.visit(item, ctx, scope) for item in node.items]

        return (VectorTypeInstance(OBJECT_TYPE, tuples), VectorType(OBJECT_TYPE))

    @visitor.when(TypeMatchingNode)
    def visit(self, node: TypeMatchingNode, ctx: Context, scope: Scope):
        value, value_type = self.visit(node.target, ctx, scope)
        node_type = get_safe_type(node.type)
        return allow_type(value_type, node_type)

    @visitor.when(DowncastingNode)
    def visit(self, node: DowncastingNode, ctx: Context, scope: Scope):
        target_value = self.visit(node.target, ctx, scope)
        node_type = get_safe_type(node.type, ctx)
        if allow_type(target_value[1], node_type):
            return target_value[0], node_type
        raise Exception(
            f"Downcasting error: {target_value[1]} does not conform to {node_type}"
        )

    @visitor.when(IndexingNode)
    def visit(self, node: IndexingNode, ctx: Context, scope: Scope):
        vector_value, vector_type = self.visit(node.target, ctx, scope)
        index, index_type = self.visit(node.index, ctx, scope)
        return vector_value[index], vector_type[index]

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, ctx: Context, scope: Scope):
        var = scope.find_variable(node.value)
        if var is not None:
            return var.value

        return (scope.find_function(node.value), FUNCTION_TYPE)

    @visitor.when(BooleanNode)
    def visit(self, node: BooleanNode, ctx: Context, scope: Scope):
        return (node.value == "true", BOOLEAN_TYPE)

    @visitor.when(NumberNode)
    def visit(self, node: NumberNode, ctx: Context, scope: Scope):
        try:
            return (int(node.value), NUMBER_TYPE)
        except ValueError:
            return (float(node.value), NUMBER_TYPE)

    @visitor.when(StringNode)
    def visit(self, node: StringNode, ctx: Context, scope: Scope):
        return (node.value, STRING_TYPE)
