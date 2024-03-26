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
