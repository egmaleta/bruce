from dataclasses import dataclass

from .tools.semantic import AST


@dataclass
class Expression(AST):
    pass


@dataclass
class Number(Expression):
    value: str


@dataclass
class String(Expression):
    value: str

    def __post_init__(self):
        self.value = self.value[1:-1]


@dataclass
class Boolean(Expression):
    value: str


@dataclass
class Identifier(Expression):
    value: str
    is_builtin: bool = False


@dataclass
class Mutation(Expression):
    id: str
    body: Expression


@dataclass
class TypeInstanceCreation(Expression):
    type: str
    args: list[Expression]


@dataclass
class Vector(Expression):
    items: list[Expression]


@dataclass
class MappedIterable(Expression):
    map_expr: Expression
    item_id: str
    item_type: str | None
    iterable_expr: Expression


@dataclass
class TypeMemberAccessing(Expression):
    target: Expression
    member_id: str


@dataclass
class FunctionCall(Expression):
    target: Expression
    args: list[Expression]


@dataclass
class Downcasting(Expression):
    target: Expression
    type: str


@dataclass
class Indexing(Expression):
    target: Expression
    index: str


@dataclass
class UnaryOperation(Expression):
    operand: Expression


@dataclass
class Negation(UnaryOperation):
    pass


@dataclass
class ArithmeticNegation(UnaryOperation):
    pass


@dataclass
class BinaryOperation(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass
class Logic(BinaryOperation):
    pass


@dataclass
class Comparison(BinaryOperation):
    pass


@dataclass
class Arithmetic(BinaryOperation):
    pass


class Powering(Arithmetic):
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, "pow", right)


@dataclass
class Concatenation(BinaryOperation):
    pass


@dataclass
class RuntimeTypeCheking(Expression):
    target: Expression
    type: str


@dataclass
class Block(Expression):
    exprs: list[Expression]


@dataclass
class Loop(Expression):
    condition: Expression
    body: Expression


@dataclass
class Iterator(Expression):
    item_id: str
    item_type: str | None
    iterable_expr: Expression
    body: Expression


@dataclass
class Conditional(Expression):
    condition_branchs: list[tuple[Expression, Expression]]
    fallback_branck: Expression


@dataclass
class LetExpression(Expression):
    id: str
    type: str | None
    value: Expression
    body: Expression


def desugar_let_expr(
    bindings: list[tuple[str, str | None, Expression]], body: Expression
):
    head, *tail = bindings
    id, type, value = head

    return LetExpression(
        id, type, value, body if len(tail) == 0 else desugar_let_expr(tail, body)
    )


@dataclass
class Function(AST):
    id: str
    params: list[tuple[str, str | None]]
    return_type: str | None
    body: Expression


@dataclass
class MethodSpec(AST):
    id: str
    params: list[tuple[str, str | None]]
    return_type: str


@dataclass
class Protocol(AST):
    type: str
    extends: list[str]
    method_specs: list[MethodSpec]
