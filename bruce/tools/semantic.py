from abc import ABC


class AST(ABC):
    pass


class VariableInfo:
    def __init__(self, name):
        self.name = name


class FunctionInfo:
    def __init__(self, name, params):
        self.name = name
        self.params = params


class Scope:
    def __init__(self, parent=None):
        self.local_vars = []
        self.local_funcs = []
        self.parent = parent
        self.children = []
        self.var_index_at_parent = 0 if parent is None else len(parent.local_vars)
        self.func_index_at_parent = 0 if parent is None else len(parent.local_funcs)

    def create_child_scope(self):
        child_scope = Scope(self)
        self.children.append(child_scope)
        return child_scope

    def define_variable(self, vname):
        existed = self.is_var_defined(vname)
        if not existed:
            self.local_vars.append(VariableInfo(vname))
        return not existed

    def define_function(self, fname, params):
        existed = self.is_func_defined(fname, len(params))
        if not existed:
            self.local_funcs.append(FunctionInfo(fname, params))
        return not existed

    def is_var_defined(self, vname):
        if self.is_local_var(vname):
            return True
        if self.parent is not None:
            for i in range(self.var_index_at_parent):
                if self.parent.local_vars[i].name == vname:
                    return True
        return False

    def is_func_defined(self, fname, n):
        if self.is_local_func(fname, n):
            return True
        if self.parent is not None:
            for i in range(self.func_index_at_parent):
                if (
                    self.parent.local_funcs[i].name == fname
                    and len(self.parent.local_funcs[i].params) == n
                ):
                    return True
        return False

    def is_local_var(self, vname):
        return self.get_local_variable_info(vname) is not None

    def is_local_func(self, fname, n):
        return self.get_local_function_info(fname, n) is not None

    def get_local_variable_info(self, vname):
        for v in self.local_vars:
            if v.name == vname:
                return v
        return None

    def get_local_function_info(self, fname, n):
        for f in self.local_funcs:
            if f.name == fname and len(f.params) == n:
                return f
        return None
