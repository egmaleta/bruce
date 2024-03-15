from dataclasses import dataclass

from .tools.semantic import ASTNode, Scope
from .tools import visitor


class ExprNode(ASTNode):
    pass


@dataclass
class LiteralNode(ExprNode):
    value: str


class NumberNode(LiteralNode):
    pass


@dataclass
class StringNode(LiteralNode):
    def __post_init__(self):
        self.value = self.value[1:-1]


class BooleanNode(LiteralNode):
    pass


@dataclass
class IdentifierNode(LiteralNode):
    is_builtin: bool = False


@dataclass
class TypeInstancingNode(ExprNode):
    type: str
    args: list[ExprNode]


@dataclass
class VectorNode(ExprNode):
    items: list[ExprNode]


@dataclass
class MappedIterableNode(ExprNode):
    map_expr: ExprNode
    item_id: str
    item_type: str | None
    iterable_expr: ExprNode


@dataclass
class MemberAccessingNode(ExprNode):
    target: ExprNode
    member_id: str


@dataclass
class FunctionCallNode(ExprNode):
    target: ExprNode
    args: list[ExprNode]


@dataclass
class IndexingNode(ExprNode):
    target: ExprNode
    index: str


@dataclass
class MutationNode(ExprNode):
    target: ExprNode
    value: ExprNode


@dataclass
class DowncastingNode(ExprNode):
    target: ExprNode
    type: str


@dataclass
class UnaryOpNode(ExprNode):
    operand: ExprNode


class NegOpNode(UnaryOpNode):
    pass


class ArithNegOpNode(UnaryOpNode):
    pass


@dataclass
class BinaryOpNode(ExprNode):
    left: ExprNode
    operator: str
    right: ExprNode


class LogicOpNode(BinaryOpNode):
    pass


class ComparisonOpNode(BinaryOpNode):
    pass


class ArithOpNode(BinaryOpNode):
    pass


class PowerOpNode(ArithOpNode):
    def __init__(self, left: ExprNode, right: ExprNode):
        super().__init__(left, "pow", right)


class ConcatOpNode(BinaryOpNode):
    def __init__(self, left: ExprNode, right: ExprNode):
        super().__init__(left, "@", right)


@dataclass
class TypeMatchingNode(ExprNode):
    target: ExprNode
    type: str


@dataclass
class BlockNode(ExprNode):
    exprs: list[ExprNode]


@dataclass
class LoopNode(ExprNode):
    condition: ExprNode
    body: ExprNode


@dataclass
class IteratorNode(ExprNode):
    item_id: str
    item_type: str | None
    iterable_expr: ExprNode
    body: ExprNode


@dataclass
class ConditionalNode(ExprNode):
    condition_branchs: list[tuple[ExprNode, ExprNode]]
    fallback_branck: ExprNode


@dataclass
class LetExprNode(ExprNode):
    id: str
    type: str | None
    value: ExprNode
    body: ExprNode


def desugar_let_expr(bindings: list[tuple[str, str | None, ExprNode]], body: ExprNode):
    head, *tail = bindings
    id, type, value = head

    return LetExprNode(
        id, type, value, body if len(tail) == 0 else desugar_let_expr(tail, body)
    )


@dataclass
class FunctionNode(ASTNode):
    id: str
    params: list[tuple[str, str | None]]
    return_type: str | None
    body: ExprNode


@dataclass
class MethodSpecNode(ASTNode):
    id: str
    params: list[tuple[str, str | None]]
    return_type: str


@dataclass
class ProtocolNode(ASTNode):
    type: str
    extends: list[str]
    method_specs: list[MethodSpecNode]


class SemanticChecker(object):
    def __init__(self):
        self.errors = []

    @visitor.on("node")
    def visit(self, node, scope):
        pass

    @visitor.when(LiteralNode)
    def visit(self, node: LiteralNode, scope: Scope):
        return self.errors

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, scope: Scope):
        if not scope.is_var_defined(node.value):
            self.errors.append(f"Variable {node.value} not defined")
        return self.errors
