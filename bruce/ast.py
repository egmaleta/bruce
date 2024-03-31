from .tools.semantic.ast import ASTNode, ExprNode
from .tools.token import Token
from dataclasses import dataclass


class ProgramNode(ASTNode):
    def __init__(self, declarations: list[ASTNode], expr: ExprNode):
        self.declarations: list[ASTNode] = declarations
        self.expr: ExprNode = expr


class LiteralNode(ExprNode):
    def __init__(self, token: Token):
        self.value = token.lex
        self.position = (token.lin, token.column)


class NumberNode(LiteralNode):
    def evaluate(self):
        return float(self.value)


class StringNode(LiteralNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.value = self.value[1:-1]

    def evaluate(self):
        return self.value


class BooleanNode(LiteralNode):
    def evaluate(self):
        return self.value == "true"


class IdentifierNode(LiteralNode):
    def __init__(self, value, is_builtin: bool = False):
        super().__init__(value)
        self.is_builtin: bool = is_builtin


class TypeInstancingNode(ExprNode):
    def __init__(self, token: Token, args: list[ExprNode]):
        self.type: str = token.lex
        self.args: list[ExprNode] = args
        self.position = (token.line, token.column)


class VectorNode(ExprNode):
    def __init__(self, items: list[ExprNode]):
        self.items: list[ExprNode] = items
        self.position = (0, 0)


class MappedIterableNode(ExprNode):
    def __init__(self, map_expr: ExprNode, item_id: Token, item_type: Token | None, iterable_expr: ExprNode):
        self.map_expr: ExprNode = map_expr
        self.item_id: str = item_id.lex
        self.item_type: str | None = item_type.lex if item_type else None
        self.iterable_expr: ExprNode = iterable_expr
        self.item_id_position = (item_id.line, item_id.column)
        self.item_type_position = (item_type.line, item_type.column) if item_type else (
            item_id.line, item_id.column)


class MemberAccessingNode(ExprNode):
    def __init__(self, target: ExprNode, member_id: Token):
        self.target: ExprNode = target
        self.member_id: str = member_id.lex
        self.position = (member_id.line, member_id.column)


class FunctionCallNode(ExprNode):
    def __init__(self, target: ExprNode, args: list[ExprNode]):
        self.target: ExprNode = target
        self.args: list[ExprNode] = args
        self.position = (target.position[0], target.position[1])


class IndexingNode(ExprNode):
    def __init__(self, target: ExprNode, index: ExprNode):
        self.target: ExprNode = target
        self.index: ExprNode = index
        self.position = (target.position[0], target.position[1])


class MutationNode(ExprNode):
    def __init__(self, target: ExprNode, value: ExprNode):
        self.target: ExprNode = target
        self.value: ExprNode = value
        self.position = (target.position[0], target.position[1])

class DowncastingNode(ExprNode):
    def __init__(self, target: ExprNode, type: Token):
        self.target: ExprNode = target
        self.type: str = type.lex
        self.position = (type.line, type.column)

class UnaryOpNode(ExprNode):
    def __init__(self, operand: ExprNode):
        self.operand: ExprNode = operand
        self.position = (operand.position[0], operand.position[1])


class NegOpNode(UnaryOpNode):
    pass


class ArithNegOpNode(UnaryOpNode):
    pass


class BinaryOpNode(ExprNode):
    def __init__(self, left: ExprNode, operator: Token, right: ExprNode):
        self.left: ExprNode = left
        self.operator: str = operator.lex
        self.right: ExprNode = right
        self.position = (left.position[0], left.position[1])


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


class TypeMatchingNode(ExprNode):
    def __init__(self, target: ExprNode, type: str):
        self.target: ExprNode = target
        self.type: str = type
        self.position = (target.position[0], target.position[1])


class BlockNode(ExprNode):
    def __init__(self, exprs: list[ExprNode]):
        self.exprs: list[ExprNode] = exprs
        self.position = (0, 0)


class LoopNode(ExprNode):
    def __init__(self, condition: ExprNode, body: ExprNode, fallback_expr: ExprNode):
        self.condition: ExprNode = condition
        self.body: ExprNode = body
        self.fallback_expr: ExprNode = fallback_expr
        self.position = (condition.position[0], condition.position[1])


class ConditionalNode(ExprNode):
    def __init__(self, condition_branchs: list[tuple[ExprNode, ExprNode]], fallback_branch: ExprNode):
        self.condition_branchs: list[tuple[ExprNode, ExprNode]] = condition_branchs
        self.fallback_branch: ExprNode = fallback_branch
        self.position = (condition_branchs[0][0].position[0],
                         condition_branchs[0][0].position[1])


class LetExprNode(ExprNode):
    def __init__(self, id: Token, type: Token | None, value: ExprNode, body: ExprNode):
        self.id = id.lex
        self.type: str | None = type.lex
        self.value: ExprNode = value
        self.body: ExprNode = body
        self.position = (id.line, id.column)


class FunctionNode(ASTNode):
    def __init__(self, id: str, params: list[tuple[str, str | None]], return_type: str | None, body: ExprNode):
        self.id: str = id
        self.params: list[tuple[str, str | None]] = params
        self.return_type: str | None = return_type
        self.body: ExprNode = body
        self.position = (0, 0)


class MethodSpecNode(ASTNode):
    def __init__(self, id: str, params: list[tuple[str, str]], return_type: str):
        self.id: str = id
        self.params: list[tuple[str, str]] = params
        self.return_type: str = return_type
        self.position = (0, 0)

class ProtocolNode(ASTNode):
    def __init__(self, type: str, extends: list[str], method_specs: list[MethodSpecNode]):
        self.type: str = type
        self.extends: list[str] = extends
        self.method_specs: list[MethodSpecNode] = method_specs
        self.position = (0, 0)


class TypePropertyNode(ASTNode):
    def __init__(self, id: Token, type: Token | None, value: ExprNode):
        self.id: str = id.lex
        self.type: str | None = type.lex
        self.value: ExprNode = value
        self.position = (id.line, id.column)


class TypeNode(ASTNode):
    def __init__(self, type: Token, params: list[tuple[Token, Token | None]] | None, parent_type: Token | None, parent_args: list[ExprNode] | None, members: list[TypePropertyNode | FunctionNode]):
        self.type: str = type.lex
        self.params: list[tuple[str, str | None]] | None = [
            (token1.lex, token2.lex) for token1, token2 in params]
        self.parent_type: str | None = parent_type.lex
        self.parent_args: list[ExprNode] | None = parent_args
        self.members: list[TypePropertyNode | FunctionNode] = members
        self.position = (type.line, type.column)


# SYNTACTIC SUGAR


@dataclass
class IteratorNode:
    """Desugars into a let expression with a loop as body."""

    item_id: str
    item_type: str | None
    iterable_expr: ExprNode
    body: ExprNode
    fallback_expr: ExprNode


@dataclass
class MultipleLetExprNode:
    """Desugars recursively into a single let expression."""

    bindings: list[tuple[str, str | None, ExprNode]]
    body: ExprNode
