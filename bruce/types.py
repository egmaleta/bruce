from typing import Union

from .tools.semantic import Type, Proto


class ObjectType(Type):
    def __init__(self):
        super().__init__("Object")


class FunctionType(Type):
    """Function type is used only for type inference and type checking
    of identifiers representing functions, like `print` or `rand`.

    It cannot be typed because its name is lowercase."""

    def __init__(self):
        super().__init__("function")

    @property
    def is_inheritable(self):
        return False


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


class VectorType(Type):
    """Vector type is used only for type inference and type checking
    of vectors, mapped iterables and indexing.

    It cannot be typed because its name is lowercase."""

    def __init__(self, item_type: Union[Type, Proto]):
        super().__init__(f"vector_of_{item_type.name}")
        self.item_type = item_type

    @property
    def is_inheritable(self):
        return False

    def __eq__(self, other):
        return isinstance(other, VectorType) and self.item_type == other.item_type


class NumberType(Type):
    def __init__(self):
        super().__init__("Number")

    @property
    def is_inheritable(self):
        return False


class BooleanType(Type):
    def __init__(self):
        super().__init__("Boolean")

    @property
    def is_inheritable(self):
        return False


class StringType(Type):
    def __init__(self):
        super().__init__("String")

    @property
    def is_inheritable(self):
        return False


OBJECT_TYPE = ObjectType()

FUNCTION_TYPE = FunctionType()

NUMBER_TYPE = NumberType()
NUMBER_TYPE.set_parent(OBJECT_TYPE)

STRING_TYPE = StringType()
STRING_TYPE.set_parent(OBJECT_TYPE)

BOOLEAN_TYPE = BooleanType()
BOOLEAN_TYPE.set_parent(OBJECT_TYPE)

ITERABLE_PROTO = Proto("Iterable")
ITERABLE_PROTO.add_method_spec("next", [], BOOLEAN_TYPE)
ITERABLE_PROTO.add_method_spec("current", [], OBJECT_TYPE)
