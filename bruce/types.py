from .tools.semantic import Type


class ObjectType(Type):
    def __init__(self):
        super().__init__("Object")


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

NUMBER_TYPE = NumberType()
NUMBER_TYPE.set_parent(OBJECT_TYPE)

STRING_TYPE = StringType()
STRING_TYPE.set_parent(OBJECT_TYPE)

BOOLEAN_TYPE = BooleanType()
BOOLEAN_TYPE.set_parent(OBJECT_TYPE)
