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
    right: Identifier
    left: Expression


@dataclass
class TypeInstanceCreation(Expression):
    type_id: str
    args: list[Expression]


@dataclass
class Vector(Expression):
    items: list[Expression]


@dataclass
class MappedIterable(Expression):
    map_expr: Expression
    item_id: str
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
    type_id: str


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


@dataclass
class Concatenation(BinaryOperation):
    pass


@dataclass
class RuntimeTypeCheking(Expression):
    target: Expression
    type_id: str
