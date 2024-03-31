from typing import Union
from typing import Any

from .tools.semantic import Type, Proto
from .names import (
    CURRENT_METHOD_NAME,
    NEXT_METHOD_NAME,
    SIZE_METHOD_NAME,
    INSTANCE_NAME,
    AT_METHOD_NAME,
    SETAT_METHOD_NAME,
)
from . import ast
from .grammar import plus, ge, eq, true_k, false_k, mod


def allow_type(type: Union[Type, Proto], type_or_proto: Union[Type, Proto]):
    if isinstance(type, Proto) and type_or_proto == OBJECT_TYPE:
        return True
    elif isinstance(type, Proto) and isinstance(type_or_proto, Proto):
        return type.extends(type_or_proto)
    elif isinstance(type, Type) and isinstance(type_or_proto, Proto):
        return type.implements(type_or_proto)
    elif isinstance(type, Type) and isinstance(type_or_proto, Type):
        return type.conforms_to(type_or_proto)
    else:
        return False


class ErrorType(Type):
    def __init__(self):
        super().__init__("errortype")

    def conforms_to(self, other):
        return True

    def bypass(self):
        return True


ERROR_TYPE = ErrorType()


class ObjectType(Type):
    def __init__(self):
        super().__init__("Object")

    def inherit_params(self):
        pass

    def set_parent(self, parent: Type):
        pass


OBJECT_TYPE = ObjectType()


class NumberType(Type):
    def __init__(self):
        super().__init__("Number")

    @property
    def is_inheritable(self):
        return False


NUMBER_TYPE = NumberType()
NUMBER_TYPE.set_parent(OBJECT_TYPE)


class BooleanType(Type):
    def __init__(self):
        super().__init__("Boolean")

    @property
    def is_inheritable(self):
        return False


BOOLEAN_TYPE = BooleanType()
BOOLEAN_TYPE.set_parent(OBJECT_TYPE)


class StringType(Type):
    def __init__(self):
        super().__init__("String")

    @property
    def is_inheritable(self):
        return False


STRING_TYPE = StringType()
STRING_TYPE.set_parent(OBJECT_TYPE)


class FunctionType(Type):
    """Function type is used only for type inference and type checking
    of identifiers representing functions, like `print` or `rand`.

    It cannot be typed because its name is lowercase."""

    def __init__(self):
        super().__init__("function")

    @property
    def is_inheritable(self):
        return False


FUNCTION_TYPE = FunctionType()


class UnionType(Type):
    """Union type is used only for type inference and type checking
    of expression with alternative branches or operators accepting multiple
    types, like conditional expressions or the concat (`@`) operator.

    It cannot be typed because its name is lowercase."""

    def __init__(self, *types: Union[Type, Proto]):
        super().__init__("union")

        self.types = set()
        for t in types:
            # unpack union types
            if isinstance(t, UnionType):
                self.types.update(t.types)
            else:
                self.types.add(t)

    @property
    def is_inheritable(self):
        return False

    def conforms_to(self, other: "Type"):
        return any(t.conforms_to(other) for t in self.types)

    def __eq__(self, other):
        return isinstance(other, UnionType) and self.types == other.types

    def __and__(self, other: Union[Type, Proto]):
        if isinstance(other, UnionType):
            return UnionType(*(self.types & other.types))

        return self.__and__(UnionType(other))

    def __or__(self, other: Union[Type, Proto]):
        if isinstance(other, UnionType):
            return UnionType(*(self.types | other.types))

        return self.__or__(UnionType(other))

    def __len__(self):
        return len(self.types)

    def __iter__(self):
        return iter(self.types)


def union_type(*types: Type) -> UnionType | Type:
    ut = UnionType(*types)
    if len(ut) == 1:
        t, *_ = ut
        return t

    return ut


class VectorType(Type):
    """Vector type is used only for type inference and type checking
    of vectors, mapped iterables and indexing.

    It cannot be typed because its name is lowercase."""

    ARG_INDEX_NAME = "i"
    ARG_VALUE_NAME = "v"

    def __init__(self, item_type: Union[Type, Proto]):
        super().__init__(f"vector_of_{item_type.name}")
        self.item_type = item_type
        self.define_method(NEXT_METHOD_NAME, [], BOOLEAN_TYPE)
        self.define_method(CURRENT_METHOD_NAME, [], item_type)
        self.define_method(SIZE_METHOD_NAME, [], NUMBER_TYPE)
        self.define_method(
            AT_METHOD_NAME, [(self.ARG_INDEX_NAME, NUMBER_TYPE)], item_type
        )
        self.define_method(
            SETAT_METHOD_NAME,
            [(self.ARG_INDEX_NAME, NUMBER_TYPE), (self.ARG_VALUE_NAME, item_type)],
            item_type,
        )
        self.set_parent(OBJECT_TYPE)

    @property
    def is_inheritable(self):
        return False

    def __eq__(self, other):
        return isinstance(other, VectorType) and self.item_type == other.item_type


class VectorTypeInstance(VectorType):
    INDEX_NAME = "index"

    def __init__(self, item_type: Type | Proto, values: list[tuple[Any, Type]]):
        super().__init__(item_type)

        attr = self.define_attribute(self.INDEX_NAME, None)
        attr.set_value((-1, NUMBER_TYPE))

        names = [f"item_at_{n}" for n in range(len(values))]
        for name, value in zip(names, values):
            attr = self.define_attribute(name, None)
            attr.set_value(value)

        size_method = self.get_method(SIZE_METHOD_NAME)
        size_method.set_body(ast.NumberNode(str(len(values))))

        next_method = self.get_method(NEXT_METHOD_NAME)
        next_method.set_body(
            ast.ConditionalNode(
                [
                    (
                        ast.ComparisonOpNode(
                            ast.ArithOpNode(
                                ast.MemberAccessingNode(
                                    ast.IdentifierNode(INSTANCE_NAME), self.INDEX_NAME
                                ),
                                plus.name,
                                ast.NumberNode("1"),
                            ),
                            ge.name,
                            ast.NumberNode(str(len(values))),
                        ),
                        ast.BooleanNode(false_k.name),
                    )
                ],
                ast.BlockNode(
                    [
                        ast.MutationNode(
                            ast.MemberAccessingNode(
                                ast.IdentifierNode(INSTANCE_NAME), self.INDEX_NAME
                            ),
                            ast.ArithOpNode(
                                ast.MemberAccessingNode(
                                    ast.IdentifierNode(INSTANCE_NAME), self.INDEX_NAME
                                ),
                                plus.name,
                                ast.NumberNode("1"),
                            ),
                        ),
                        ast.BooleanNode(true_k.name),
                    ]
                ),
            )
        )

        current_method = self.get_method(CURRENT_METHOD_NAME)
        current_method.set_body(
            ast.LetExprNode(
                "x",
                NUMBER_TYPE.name,
                ast.MemberAccessingNode(
                    ast.IdentifierNode(INSTANCE_NAME), self.INDEX_NAME
                ),
                ast.ConditionalNode(
                    [
                        (
                            ast.ComparisonOpNode(
                                ast.IdentifierNode("x"), eq.name, ast.NumberNode(str(i))
                            ),
                            ast.MemberAccessingNode(
                                ast.IdentifierNode(INSTANCE_NAME), name
                            ),
                        )
                        for i, name in enumerate(names)
                    ],
                    ast.MemberAccessingNode(
                        ast.IdentifierNode(INSTANCE_NAME), names[-1]
                    ),
                ),
            )
        )

        at_method = self.get_method(AT_METHOD_NAME)
        at_method.set_body(
            ast.LetExprNode(
                self.ARG_INDEX_NAME,
                NUMBER_TYPE.name,
                ast.ArithOpNode(
                    ast.IdentifierNode(self.ARG_INDEX_NAME),
                    mod.name,
                    ast.NumberNode(str(len(values))),
                ),
                ast.ConditionalNode(
                    [
                        (
                            ast.ComparisonOpNode(
                                ast.IdentifierNode(self.ARG_INDEX_NAME),
                                eq.name,
                                ast.NumberNode(str(i)),
                            ),
                            ast.MemberAccessingNode(
                                ast.IdentifierNode(INSTANCE_NAME), name
                            ),
                        )
                        for i, name in enumerate(names)
                    ],
                    ast.MemberAccessingNode(
                        ast.IdentifierNode(INSTANCE_NAME), names[-1]
                    ),
                ),
            )
        )

        setat_method = self.get_method(SETAT_METHOD_NAME)
        setat_method.set_body(
            ast.LetExprNode(
                self.ARG_INDEX_NAME,
                NUMBER_TYPE.name,
                ast.ArithOpNode(
                    ast.IdentifierNode(self.ARG_INDEX_NAME),
                    mod.name,
                    ast.NumberNode(str(len(values))),
                ),
                ast.ConditionalNode(
                    [
                        (
                            ast.ComparisonOpNode(
                                ast.IdentifierNode(self.ARG_INDEX_NAME),
                                eq.name,
                                ast.NumberNode(str(i)),
                            ),
                            ast.MutationNode(
                                ast.MemberAccessingNode(
                                    ast.IdentifierNode(INSTANCE_NAME), name
                                ),
                                ast.IdentifierNode(self.ARG_VALUE_NAME),
                            ),
                        )
                        for i, name in enumerate(names)
                    ],
                    ast.IdentifierNode(self.ARG_VALUE_NAME),
                ),
            )
        )


ITERABLE_PROTO = Proto("Iterable")
ITERABLE_PROTO.add_method_spec(NEXT_METHOD_NAME, [], BOOLEAN_TYPE)
ITERABLE_PROTO.add_method_spec(CURRENT_METHOD_NAME, [], OBJECT_TYPE)
