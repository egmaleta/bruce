from ..tools.semantic import visitor as visitor
from ..types import NUMBER_TYPE, STRING_TYPE, OBJECT_TYPE, BOOLEAN_TYPE
from ..tools.semantic.context import Context, get_safe_type
from ..tools.semantic.scope import Scope
from ..ast import *


class Evaluator:
    def __init__(self, errors=[]) -> None:
        self.errors = errors

    @visitor.on("node")
    def visit(self, node, context: Context, scope: Scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, ctx: Context, scope: Scope):
        self.visit(node.expr, ctx, scope)
        return self.errors

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context, scope: Scope):
        pass

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
        pass

    @visitor.when(PowerOpNode)
    def visit(self, node: PowerOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ComparisonOpNode)
    def visit(self, node: ComparisonOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ConcatOpNode)
    def visit(self, node: ConcatOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(LogicOpNode)
    def visit(self, node: LogicOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(ArithNegOpNode)
    def visit(self, node: ArithNegOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(NegOpNode)
    def visit(self, node: NegOpNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(MappedIterableNode)
    def visit(self, node: MappedIterableNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(TypeMatchingNode)
    def visit(self, node: TypeMatchingNode, ctx: Context, scope: Scope):
        pass

    @visitor.when(DowncastingNode)
    def visit(self, node: DowncastingNode, ctx: Context, scope: Scope):
        target_value = self.visit(node.target, ctx, scope)
        node_type = get_safe_type(node.type, ctx)

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
