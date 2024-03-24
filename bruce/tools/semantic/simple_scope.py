class Scope:
    def __init__(self, parent: "Scope" | None = None):
        self.parent = parent
        self.variables: dict[str, Variable] = {}
        self.functions: dict[str, Function] = {}

    def create_child(self):
        return Scope(self)

    def get_variable(self, name: str):
        v = self.variables.get(name)
        if v is not None:
            return v

        if self.parent is not None:
            return self.parent.get_variable(name)

    def has_variable(self, name: str):
        return self.get_variable(name) is not None

    def create_variable(self, name: str, type: Type | None):
        if self.has_variable(name):
            raise SemanticError(f"variable '{name}' is already defined")

        v = Variable(name, type)
        self.variables[name] = v
        return v

    def mutate_variable(self, name: str, value: Any):
        v = self.get_variable(name)
        if v is None:
            raise SemanticError(f"variable '{name}' hasn't been defined")

        if v.is_mutable():
            v.value = value
            return True

        return False
