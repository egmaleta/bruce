from collections import OrderedDict
from typing import Union, Any


class SemanticError(Exception):
    @property
    def text(self):
        return self.args[0]


class Variable:
    def __init__(
        self,
        name: str,
        type: Union["Type", "Proto", None] = None,
        value: tuple[Any, "Type"] = None,
        *,
        owner_scope=None,
    ):
        self.name = name
        self.type = type
        self._label = "[var]"

        self.owner_scope = owner_scope
        self.value = value

    @property
    def is_mutable():
        return True

    def set_type(self, type: Union["Type", "Proto"]):
        self.type = type

    def set_value(self, value: tuple[Any, "Type"]):
        self.value = value

    def __str__(self):
        typename = self.type.name if self.type is not None else "Unknown"
        return f"{self._label} {self.name} : {typename};"

    def __repr__(self):
        return str(self)


class Attribute(Variable):
    def __init__(
        self,
        name: str,
        type: Union["Type", "Proto", None] = None,
        value: tuple[Any, "Type"] = None,
    ):
        super().__init__(name, type, value)
        self._label = "[attrib]"


class Constant(Variable):
    def __init__(
        self, name: str, type: Union["Type", "Proto"], value: tuple[Any, "Type"]
    ):
        super().__init__(name, type, value)
        self._label = "[const]"

    def set_value(self, value: tuple[Any, "Type"]):
        raise SemanticError(f"Constant '{self.name}' is inmutable.")

    @property
    def is_mutable(self):
        return False


class Function:
    def __init__(
        self,
        name: str,
        params: list[tuple[str, Union["Type", "Proto", None]]],
        type: Union["Type", "Proto", None] = None,
    ):
        self.name = name
        self.params = OrderedDict(params)
        self.type = type
        self._label = "[func]"

    def set_type(self, type: Union["Type", "Proto"]):
        if self.type is None:
            self.type = type

    def set_param_type(self, name: str, type: Union["Type", "Proto"]):
        if name in self.params and self.params[name] is None:
            self.params[name] = type

    def __str__(self):
        params = []
        for name, type in self.params.items():
            typename = type.name if type is not None else "Unknown"
            params.append(f"{name}: {typename}")
        params = ", ".join(params)

        typename = self.type.name if self.type is not None else "Unknown"

        return f"{self._label} {self.name}({params}): {typename};"


class Method(Function):
    def __init__(
        self,
        name: str,
        params: list[tuple[str, Union["Type", "Proto", None]]],
        type: Union["Type", "Proto", None] = None,
    ):
        super().__init__(name, params, type)
        self._label = "[method]"


class Type:
    def __init__(self, name: str):
        self.name = name
        self.params: OrderedDict[str, Union["Type", "Proto", None]] = OrderedDict()

        self.attributes: list[Attribute] = []
        self.methods: list[Method] = []

        self.parent: Type | None = None

    def set_params(self, params: list[tuple[str, Union["Type", "Proto", None]]]):
        if len(self.params) > 0:
            raise SemanticError(f"Params are already set for type '{self.name}'.")

        for name, type in params:
            if name in self.params:
                raise SemanticError(
                    f"Param '{name}' is duplicated in constructor of type '{self.name}'."
                )
            self.params[name] = type

    def inherit_params(self):
        if len(self.params) == 0 and self.parent is not None:
            self.parent.inherit_params()
            for name, pt in self.parent.params.items():
                self.params[name] = pt

    def set_param_type(self, name: str, type: Union["Type", "Proto"]):
        if name in self.params and self.params[name] is None:
            self.params[name] = type

    def get_attribute(self, name: str):
        target = None
        for attr in self.attributes:
            if attr.name == name:
                target = attr
                break

        if target is not None:
            return target

        raise SemanticError(f"Attribute '{name}' is not defined in type '{self.name}'.")

    def define_attribute(self, name: str, type: Union["Type", "Proto", None]):
        try:
            self.get_attribute(name)
        except SemanticError:
            attribute = Attribute(name, type)
            self.attributes.append(attribute)
            return attribute
        else:
            raise SemanticError(
                f"Attribute '{name}' is already defined in type '{self.name}'."
            )

    def get_method(self, name: str):
        target = None
        for attr in self.methods:
            if attr.name == name:
                target = attr
                break

        if target is not None:
            return target

        if self.parent is None:
            raise SemanticError(f'Method "{name}" is not defined in {self.name}.')
        try:
            return self.parent.get_method(name)
        except SemanticError:
            raise SemanticError(f'Method "{name}" is not defined in {self.name}.')

    def define_method(
        self,
        name: str,
        params: list[tuple[str, Union["Type", "Proto", None]]],
        type: Union["Type", "Proto", None] = None,
    ):
        try:
            self.get_method(name)
        except SemanticError:
            method = Method(name, params, type)
            self.methods.append(method)
            return method
        else:
            raise SemanticError(
                f"Method '{name}' is already defined in type '{self.name}'."
            )

    @property
    def is_inheritable(self):
        return True

    def conforms_to(self, other: "Type"):
        if self == other:
            return True

        if not other.is_inheritable:
            return False

        return self.parent is not None and self.parent.conforms_to(other)

    def implements(self, proto: "Proto"):
        for spec in proto.all_method_specs():
            try:
                method = self.get_method(spec.name)
            except SemanticError:
                return False
            else:
                if len(method.params) != len(spec.params):
                    return False

                # spec param <= method param
                for pt, spt in zip(method.params.values(), spec.params.values()):
                    if pt is None:
                        continue

                    pt_is_type = isinstance(pt, Type)
                    spt_is_type = isinstance(spt, Type)
                    pt_is_proto = not pt_is_type
                    spt_is_proto = not spt_is_type
                    if (
                        (pt_is_type and spt_is_type and not spt.conforms_to(pt))
                        or (pt_is_type and spt_is_proto and not pt.implements(spt))
                        or (pt_is_proto and spt_is_proto and not pt.extends(spt))
                        or (pt_is_proto and spt_is_type)
                    ):
                        return False

                # method type <= spec type
                if method.type is not None:
                    mt_is_type = isinstance(method.type, Type)
                    st_is_type = isinstance(spec.type, Type)
                    mt_is_proto = not mt_is_type
                    st_is_proto = not st_is_type
                    if (
                        (
                            mt_is_type
                            and spt_is_type
                            and not method.type.conforms_to(spec.type)
                        )
                        or (
                            mt_is_type
                            and st_is_proto
                            and not method.type.implements(spec.type)
                        )
                        or (
                            mt_is_proto
                            and st_is_proto
                            and not method.type.extends(spec.type)
                        )
                        or (mt_is_proto and st_is_type)
                    ):
                        return False

        return True

    def set_parent(self, parent: "Type"):
        if self.parent is not None:
            raise SemanticError(f"Parent type is already set for type '{self.name}'.")
        self.parent = parent

    def all_attributes(self, clean=True):
        plain = (
            OrderedDict() if self.parent is None else self.parent.all_attributes(False)
        )
        for attr in self.attributes:
            plain[attr.name] = (attr, self)
        return plain.values() if clean else plain

    def all_methods(self, clean=True):
        plain = OrderedDict() if self.parent is None else self.parent.all_methods(False)
        for method in self.methods:
            plain[method.name] = (method, self)
        return plain.values() if clean else plain

    def __str__(self):
        output = f"type {self.name}"
        parent = "" if self.parent is None else f" : {self.parent.name}"
        output += parent
        output += " {"
        output += "\n\t" if self.attributes or self.methods else ""
        output += "\n\t".join(str(x) for x in self.attributes)
        output += "\n\t" if self.attributes else ""
        output += "\n\t".join(str(x) for x in self.methods)
        output += "\n" if self.methods else ""
        output += "}\n"
        return output

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, Type) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __deep_copy__(self, memo):
        if self in memo:
            return memo[self]

        new_type = Type(self.name)
        memo[self] = new_type

        new_type.parent = self.parent
        new_type.params = {k: v for k, v in self.params.items()}
        new_type.attributes = [x.__deep_copy__(memo) for x in self.attributes]
        new_type.methods = [x.__deep_copy__(memo) for x in self.methods]

        return new_type


class MethodSpec:
    def __init__(
        self,
        name: str,
        params: list[tuple[str, Union["Type", "Proto"]]],
        type: Union["Type", "Proto"],
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
        params: list[tuple[str, Union["Type", "Proto"]]],
        type: Union["Type", "Proto"],
    ):
        spec = MethodSpec(name, params, type)
        if spec not in self._all_method_specs():
            self.method_specs.append(spec)

    def all_method_specs(self):
        return list(self._all_method_specs())

    def extends(self, other):
        return other in self._ancestors()

    def __eq__(self, other):
        return isinstance(other, Proto) and self.name == other.name

    def __hash__(self):
        return hash(self.name)
