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


class MethodSpec:
    def __init__(
        self,
        name: str,
        params: list[tuple[str, "Type" | "Proto"]],
        type: "Type" | "Proto",
    ):
        self.name = name
        self.params = OrderedDict(params)
        self.type = type

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Proto:
    def __init__(self, name: str):
        self.name = name
        self.parents: list[Proto] = []
        self.method_specs: list[MethodSpec] = []

    def _ancestors(self) -> set["Proto"]:
        ancestors = set()

        for parent in self.parents:
            ancestors.add(parent)
            ancestors |= parent._ancestors()

        return ancestors

    def _all_method_specs(self) -> set[MethodSpec]:
        specs = set()

        for ancestor in self._ancestors():
            specs |= ancestor._all_method_specs()

        for spec in self.method_specs:
            specs.add(spec)

        return specs

    def add_parent(self, parent: "Proto"):
        ancestors = self._ancestors()
        parent_ancestors = parent._ancestors()

        cond = self not in parent_ancestors
        cond = cond and parent not in ancestors
        cond = cond and len(ancestors & parent_ancestors) == 0
        cond = cond and len(self._all_method_specs() & parent._all_method_specs()) == 0

        if cond:
            self.parents.append(parent)

    def add_method_spec(
        self,
        name: str,
        params: list[tuple[str, "Type" | "Proto"]],
        type: "Type" | "Proto",
    ):
        spec = MethodSpec(name, params, type)
        if spec not in self._all_method_specs():
            self.method_specs.append(spec)

    def all_method_specs(self):
        return list(self._all_method_specs())

    def extends(self, other):
        return other in self._ancestors()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
