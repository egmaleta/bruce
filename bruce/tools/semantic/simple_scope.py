from collections import OrderedDict
from typing import Union, Any

from . import Variable, Constant, Function, Type, Proto, SemanticError


class Scope:
    def __init__(self, parent: Union["Scope", None] = None, *, is_function_scope=False):
        self.parent = parent

        self.local_vars: OrderedDict[str, Variable] = OrderedDict()
        self.local_funcs: OrderedDict[str, Function] = OrderedDict()

        self.is_function_scope = is_function_scope

    def create_child(self, *, is_function_scope=False):
        return Scope(self, is_function_scope=is_function_scope)

    def define_variable(
        self,
        name: str,
        type: Union[Type, Proto, None] = None,
        value: tuple[Any, Type] = None,
    ):
        if name in self.local_vars:
            raise SemanticError(f"Variable '{name}' already defined in scope.")

        var = Variable(name, type, value, owner_scope=self)
        self.local_vars[name] = var

        return var

    def define_constant(
        self, name: str, type: Union[Type, Proto], value: tuple[Any, Type]
    ):
        if name in self.local_vars:
            raise SemanticError(f"Constant '{name}' already defined in scope.")

        const = Constant(name, type, value)
        self.local_vars[name] = const

        return const

    def define_function(
        self,
        name: str,
        params: list[tuple[str, Union[Type, Proto, None]]],
        type: Union[Type, Proto, None] = None,
    ):
        if name in self.local_funcs:
            raise SemanticError(f"Function '{name}' already defined in scope.")

        f = Function(name, params, type)
        self.local_funcs[name] = f

        return f

    def find_variable(self, name: str):
        if name in self.local_vars:
            return self.local_vars[name]

        if self.parent is not None:
            return self.parent.find_variable(name)

        return None

    def find_function(self, name: str):
        if name in self.local_funcs:
            return self.local_funcs[name]

        if self.parent is not None:
            return self.parent.find_function(name)

        return None

    def is_var_defined(self, name: str):
        return self.find_variable(name) is not None

    def is_func_defined(self, name: str):
        return self.find_function(name) is not None

    def get_top_scope(self):
        if self.parent is None:
            return self

        return self.parent.get_top_scope()
