from itertools import islice


class Scope:
    def __init__(self, parent=None):
        self.local_vars = []
        self.local_funcs = []
        self.parent = parent
        self.children = []
        self.index = 0 if parent is None else len(parent)

    def __len__(self):
        return len(self.locals)

    def create_child(self):
        child = Scope(self)
        self.children.append(child)
        return child

    def define_variable(self, vname, vtype):
        info = VariableInfo(vname, vtype)
        self.local_vars.append(info)
        return info

    def define_function(self, fname, params, type, body):
        info = FunctionInfo(fname, params)
        self.local_funcs.append(info)
        return info

    def find_variable(self, vname, index=None):
        locals = self.local_vars if index is None else islice(self.locals, index)
        try:
            return next(x for x in locals if x.name == vname)
        except StopIteration:
            return (
                self.parent.find_variable(vname, self.index)
                if self.parent != None
                else None
            )

    def find_function(self, fname, params, body, index=None):
        local_funcs = self.local_funcs if index is None else islice(self.locals, index)
        try:
            return next(x for x in local_funcs if x.name)
        except StopIteration:
            return (
                self.parent.find_function(fname, params, body, self.index)
                if self.parent != None
                else None
            )

    def is_defined(self, vname):
        return self.find_variable(vname) is not None

    def is_local(self, vname):
        return any(True for x in self.locals if x.name == vname)
