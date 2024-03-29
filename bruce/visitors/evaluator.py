from ..tools import visitor
from ..tools.semantic import Type, Method, Proto
from ..types import (
    NUMBER_TYPE,
    STRING_TYPE,
    OBJECT_TYPE,
    BOOLEAN_TYPE,
    UnionType,
    VectorType,
)
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from ..ast import *


class Evaluator:
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

        self.current_type = None

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        is_method = self.current_method is not None

        if is_method:
            self.current_method.set_body(node.body)
        else:
            f = scope.find_function(node.id)
            f.set_body(node.id)

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        attr = self.current_type.get_attribute(node.id)
        attr.set_init_expr(node.value)

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(MemberAccessingNode)
    def visit(self, node: MemberAccessingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(FunctionCallNode)
    def visit(self, node: FunctionCallNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ConditionalNode)
    def visit(self, node: ConditionalNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(LoopNode)
    def visit(self, node: LoopNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ArithOpNode)
    def visit(self, node: ArithOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)
        print(node.operator)
        funcs = {
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
            "/": lambda x, y: x / y,
            "%": lambda x, y: x % y,
        }
        v = funcs[node.operator](left_value, right_value)
        print(v)

    @visitor.when(PowerOpNode)
    def visit(self, node: PowerOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)
        return left_value**right_value

    @visitor.when(ComparisonOpNode)
    def visit(self, node: ComparisonOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)
        funcs = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            ">=": lambda x, y: x >= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
        }
        return funcs[node.operator](left_value, right_value)

    @visitor.when(ConcatOpNode)
    def visit(self, node: ConcatOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(LogicOpNode)
    def visit(self, node: LogicOpNode, ctx: Context, scope: Scope):
        left_value, left_type = self.visit(node.left, ctx, scope)
        right_value, right_type = self.visit(node.right, ctx, scope)
        funcs = {
            "&": lambda x, y: x and y,
            "|": lambda x, y: x or y,
        }
        return funcs[node.operator](left_value, right_value)

    @visitor.when(ArithNegOpNode)
    def visit(self, node: ArithNegOpNode, ctx: Context, scope: Scope):
        value, node_type = self.visit(node.operand, ctx, scope)
        return -value

    @visitor.when(NegOpNode)
    def visit(self, node: NegOpNode, ctx: Context, scope: Scope):
        value, node_type = self.visit(node.operand, ctx, scope)
        return not value

    @visitor.when(MappedIterableNode)
    def visit(self, node: MappedIterableNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, ctx: Context, scope: Scope):
        tuples = [self.visit(item, ctx, scope) for item in node.items]

        values = []
        types = []
        for v, t in tuples:
            values.append(v)
            types.append(t)

        t = UnionType(*types)
        if len(t) == 1:
            t, *_ = t

        return (values, VectorType(t))

    @visitor.when(TypeMatchingNode)
    def visit(self, node: TypeMatchingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(DowncastingNode)
    def visit(self, node: DowncastingNode, ctx: Context, scope: Scope):
        target_value = self.visit(node.target, ctx, scope)
        node_type = get_safe_type(node.type, ctx)
        if (
            target_value[1] is Type
            and target_value[1].conforms_to(node_type)
            or target_value[1] is Proto
            and target_value[1].implements(node_type)
        ):
            return target_value[0], node_type
        raise Exception(
            f"Downcasting error: {target_value[1]} does not conform to {node_type}"
        )

    @visitor.when(IndexingNode)
    def visit(self, node: IndexingNode, ctx: Context, scope: Scope):
        vector_value = self.visit(node.target, ctx, scope)
        index = self.visit(node.index, ctx, scope)
        return vector_value[index]

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, ctx: Context, scope: Scope):
        try:
            return scope.find_variable(node.value).value
        except AttributeError as ae:
            return scope.find_function(node.value).body

    @visitor.when(BooleanNode)
    def visit(self, node: BooleanNode, ctx: Context, scope: Scope):
        return True if node.value == "true" else False

    @visitor.when(NumberNode)
    def visit(self, node: NumberNode, ctx: Context, scope: Scope):
        return (float(node.value), NUMBER_TYPE)

    @visitor.when(StringNode)
    def visit(self, node: StringNode, ctx: Context, scope: Scope):
        return (node.value, STRING_TYPE)
