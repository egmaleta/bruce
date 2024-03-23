from abc import ABC
from collections import OrderedDict


class ASTNode(ABC):
    pass


class ExprNode(ASTNode):
    pass


class SemanticError(Exception):
    @property
    def text(self):
        return self.args[0]


class VariableInfo:
    def __init__(self, name: str, type: "Type" | None = None):
        self.name = name
        self.type = type
        self._label = "[var]"

    @property
    def is_mutable():
        return True

    def set_type(self, type: "Type"):
        if self.type == None:
            self.type = type

    def __str__(self):
        typename = self.type.name if self.type != None else "Unknown"
        return f"{self._label} {self.name} : {typename};"

    def __repr__(self):
        return str(self)


class AttributeInfo(VariableInfo):
    def __init__(self, name: str, type: "Type"):
        super().__init__(name, type)
        self._label = "[attrib]"


class ConstantInfo(VariableInfo):
    def __init__(self, name: str, type: "Type"):
        super().__init__(name, type)
        self._label = "[const]"

    @property
    def is_mutable(self):
        return False


class FunctionInfo:
    def __init__(
        self,
        name: str,
        params: list[tuple[str, "Type" | None]],
        body: ExprNode,
        type: "Type" | None = None,
    ):
        self.name = name
        self.params = OrderedDict(params)
        self.type = type
        self.body = body
        self._label = "[func]"

    def set_type(self, type: "Type"):
        if self.type == None:
            self.type = type

    def set_param_type(self, name: str, type: "Type"):
        if name in self.params and self.params[name] == None:
            self.params[name] = type

    def __str__(self):
        params = []
        for name, type in self.params.items():
            typename = type.name if type != None else "Unknown"
            params.append(f"{name}: {typename}")
        params = ", ".join(params)

        typename = self.type.name if self.type != None else "Unknown"

        return f"{self._label} {self.name}({params}): {typename};"


class MethodInfo(FunctionInfo):
    def __init__(
        self,
        name: str,
        params: list[tuple[str, "Type" | None]],
        body: ExprNode,
        type: "Type" | None = None,
    ):
        super().__init__(name, params, type, body)
        self._label = "[method]"
