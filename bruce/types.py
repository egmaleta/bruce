from .tools.semantic.context import Type


class NumberType(Type):
    def __init__(self):
        super().__init__(self, "Number")

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, NumberType)


class BooleanType(Type):
    def __init__(self):
        super().__init__(self, "Boolean")

    def __eq__(self, other) -> bool:
        return other.name == self.name or isinstance(other, BooleanType)


class StringType(Type):
    def __init__(self):
        super().__init__(self, "String")

    def __eq__(self, other) -> bool:
        return other.name == self.name or isinstance(other, StringType)
