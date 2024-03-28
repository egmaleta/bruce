from typing import Union

from .tools.semantic import Type, Proto
from .names import CURRENT_METHOD_NAME, NEXT_METHOD_NAME, SIZE_METHOD_NAME


class ObjectType(Type):
    def __init__(self):
        super().__init__("Object")


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


class VectorType(Type):
    """Vector type is used only for type inference and type checking
    of vectors, mapped iterables and indexing.

    It cannot be typed because its name is lowercase."""

    def __init__(self, item_type: Union[Type, Proto]):
        super().__init__(f"vector_of_{item_type.name}")
        self.item_type = item_type
        self.define_method(NEXT_METHOD_NAME, [], BOOLEAN_TYPE)
        self.define_method(CURRENT_METHOD_NAME, [], item_type)
        self.define_method(SIZE_METHOD_NAME, [], NUMBER_TYPE)
        self.set_parent(OBJECT_TYPE)

    @property
    def is_inheritable(self):
        return False

    def __eq__(self, other):
        return isinstance(other, VectorType) and self.item_type == other.item_type


ITERABLE_PROTO = Proto("Iterable")
ITERABLE_PROTO.add_method_spec(NEXT_METHOD_NAME, [], BOOLEAN_TYPE)
ITERABLE_PROTO.add_method_spec(CURRENT_METHOD_NAME, [], OBJECT_TYPE)
