from collections import OrderedDict

from . import SemanticError


class Attribute:
    def __init__(self, name: str, typex: "Type"):
        self.name = name
        self.type = typex

    def __str__(self):
        return f"[attrib] {self.name} : {self.type.name};"

    def __repr__(self):
        return str(self)


class Method:
    def __init__(
        self,
        name: str,
        param_names: list[str],
        params_types: list["Type" | None],
        return_type: "Type" | None,
    ):
        self.name = name
        self.param_names = param_names
        self.param_types = params_types
        self.return_type = return_type

    def __str__(self):
        params = ", ".join(
            f"{n}:{t.name}" for n, t in zip(self.param_names, self.param_types)
        )
        return f"[method] {self.name}({params}): {self.return_type.name};"

    def __eq__(self, other):
        return (
            other.name == self.name
            and other.return_type == self.return_type
            and other.param_types == self.param_types
        )


class Type:
    def __init__(self, name: str):
        self.name = name
        self.attributes: list[Attribute] = []
        self.methods: list[Method] = []
        self.parent: Type | None = None

    def set_parent(self, parent: "Type"):
        if self.parent is not None:
            raise SemanticError(f"Parent type is already set for {self.name}.")
        self.parent = parent

    def get_attribute(self, name: str):
        try:
            return next(attr for attr in self.attributes if attr.name == name)
        except StopIteration:
            if self.parent is None:
                raise SemanticError(
                    f'Attribute "{name}" is not defined in {self.name}.'
                )
            try:
                return self.parent.get_attribute(name)
            except SemanticError:
                raise SemanticError(
                    f'Attribute "{name}" is not defined in {self.name}.'
                )

    def define_attribute(self, name: str, typex: "Type"):
        try:
            self.get_attribute(name)
        except SemanticError:
            attribute = Attribute(name, typex)
            self.attributes.append(attribute)
            return attribute
        else:
            raise SemanticError(
                f'Attribute "{name}" is already defined in {self.name}.'
            )

    def get_method(self, name: str):
        try:
            return next(method for method in self.methods if method.name == name)
        except StopIteration:
            if self.parent is None:
                raise SemanticError(f'Method "{name}" is not defined in {self.name}.')
            try:
                return self.parent.get_method(name)
            except SemanticError:
                raise SemanticError(f'Method "{name}" is not defined in {self.name}.')

    def define_method(
        self,
        name: str,
        param_names: list[str],
        param_types: list["Type"],
        return_type: "Type" | None,
    ):
        if name in (method.name for method in self.methods):
            raise SemanticError(f'Method "{name}" already defined in {self.name}')

        method = Method(name, param_names, param_types, return_type)
        self.methods.append(method)
        return method

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

    def conforms_to(self, other: "Type"):
        return (
            other.bypass()
            or self == other
            or self.parent is not None
            and self.parent.conforms_to(other)
        )

    def bypass(self):
        return False

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
    

class Protocol:
    def __init__(self, name:str) -> None:
        self.name = name
        self.parents:list[Protocol] = []
        self.methods: list[Method] = []

    def __eq__(self, __value: object) -> bool:
        return self.name == __value.name


    def extends(self, other) -> bool:
        if other in self.parents:
            return True
        
        return any(parent.extends(other) for parent in self.parents)
        


class Context:
    def __init__(self):
        self.types = {}

    def create_type(self, name: str):
        if name in self.types:
            raise SemanticError(f"Type with the same name ({name}) already in context.")
        typex = self.types[name] = Type(name)
        return typex

    def get_type(self, name: str):
        try:
            return self.types[name]
        except KeyError:
            raise SemanticError(f'Type "{name}" is not defined.')

    def __str__(self):
        return (
            "{\n\t"
            + "\n\t".join(y for x in self.types.values() for y in str(x).split("\n"))
            + "\n}"
        )

    def __repr__(self):
        return str(self)
