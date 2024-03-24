from .tools.semantic import ASTNode, ExprNode
from dataclasses import dataclass
from typing import Union


@dataclass
class ProgramNode(ASTNode):
    declarations: list[ASTNode]
    expr: ExprNode


@dataclass
class LiteralNode(ExprNode):
    value: str


class NumberNode(LiteralNode):
    def evaluate(self):
        return float(self.value)


@dataclass
class StringNode(LiteralNode):
    def __post_init__(self):
        self.value = self.value[1:-1]

    def evaluate(self):
        return self.value


class BooleanNode(LiteralNode):
    def evaluate(self):
        return self.value == "true"


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
    index: ExprNode


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
    fallback_expr: ExprNode


@dataclass
class IteratorNode(ExprNode):
    item_id: str
    item_type: str | None
    iterable_expr: ExprNode
    body: ExprNode
    fallback_expr: ExprNode


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
    params: list[tuple[str, str]]
    return_type: str


@dataclass
class ProtocolNode(ASTNode):
    type: str
    extends: list[str]
    method_specs: list[MethodSpecNode]


@dataclass
class TypePropertyNode(ASTNode):
    id: str
    type: str | None
    value: ExprNode


@dataclass
class TypeNode(ASTNode):
    type: str
    params: list[tuple[str, str | None]] | None
    parent_type: str | None
    parent_args: list[ExprNode] | None
    members: list[TypePropertyNode | FunctionNode]


def is_assignable(node: ASTNode):
    is_assignable_id = isinstance(node, IdentifierNode) and (not node.is_builtin)
    return is_assignable_id or isinstance(node, (IndexingNode, MemberAccessingNode))
