from . import SemanticError, Type, Proto


class Context:
    def __init__(self):
        self.types: dict[str, Type] = {}
        self.protocols: dict[str, Proto] = {}

    def create_type(self, name: str):
        if name in self.types:
            raise SemanticError(f"Type with the same name '{name}' already in context.")
        type = self.types[name] = Type(name)
        return type

    def get_type(self, name: str):
        type = self.types.get(name)
        if type is None:
            raise SemanticError(f"Type '{name}' is not defined.")

        return type

    def create_protocol(self, name: str):
        if name in self.protocols:
            raise SemanticError(
                f"Protocol with the same name '{name}' already in context."
            )
        protocol = self.protocols[name] = Proto(name)
        return protocol

    def get_protocol(self, name: str):
        protocol = self.protocols.get(name)
        if protocol is None:
            raise SemanticError(f"Protocol '{name}' is not defined.")

        return protocol

    def __str__(self):
        return (
            "{\n\t"
            + "\n\t".join(y for x in self.types.values() for y in str(x).split("\n"))
            + "\n\t".join(
                y for x in self.protocols.values() for y in str(x).split("\n")
            )
            + "\n}"
        )

    def __repr__(self):
        return str(self)
