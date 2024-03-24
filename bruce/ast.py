from dataclasses import dataclass
from typing import Union

from .tools.semantic import ASTNode, ExprNode, SemanticError, Type, Proto
from .tools.semantic.context import Context
from .tools.semantic.scope import Scope
from .tools import visitor


@dataclass
class ProgramNode(ASTNode):
    declarations: list[ASTNode]
    expr: ExprNode


@dataclass
class LiteralNode(ExprNode):
    value: str


class NumberNode(LiteralNode):
    def evaluate(self):
        return float(self.value)


@dataclass
class StringNode(LiteralNode):
    def __post_init__(self):
        self.value = self.value[1:-1]

    def evaluate(self):
        return self.value


class BooleanNode(LiteralNode):
    def evaluate(self):
        return self.value == "true"


@dataclass
class IdentifierNode(LiteralNode):
    is_builtin: bool = False


@dataclass
class TypeInstancingNode(ExprNode):
    type: str
    args: list[ExprNode]


@dataclass
class VectorNode(ExprNode):
    items: list[ExprNode]


@dataclass
class MappedIterableNode(ExprNode):
    map_expr: ExprNode
    item_id: str
    item_type: str | None
    iterable_expr: ExprNode


@dataclass
class MemberAccessingNode(ExprNode):
    target: ExprNode
    member_id: str


@dataclass
class FunctionCallNode(ExprNode):
    target: ExprNode
    args: list[ExprNode]


@dataclass
class IndexingNode(ExprNode):
    target: ExprNode
    index: ExprNode


@dataclass
class MutationNode(ExprNode):
    target: ExprNode
    value: ExprNode


@dataclass
class DowncastingNode(ExprNode):
    target: ExprNode
    type: str


@dataclass
class UnaryOpNode(ExprNode):
    operand: ExprNode


class NegOpNode(UnaryOpNode):
    pass


class ArithNegOpNode(UnaryOpNode):
    pass


@dataclass
class BinaryOpNode(ExprNode):
    left: ExprNode
    operator: str
    right: ExprNode


class LogicOpNode(BinaryOpNode):
    pass


class ComparisonOpNode(BinaryOpNode):
    pass


class ArithOpNode(BinaryOpNode):
    pass


class PowerOpNode(ArithOpNode):
    def __init__(self, left: ExprNode, right: ExprNode):
        super().__init__(left, "pow", right)


class ConcatOpNode(BinaryOpNode):
    def __init__(self, left: ExprNode, right: ExprNode):
        super().__init__(left, "@", right)


@dataclass
class TypeMatchingNode(ExprNode):
    target: ExprNode
    type: str


@dataclass
class BlockNode(ExprNode):
    exprs: list[ExprNode]


@dataclass
class LoopNode(ExprNode):
    condition: ExprNode
    body: ExprNode
    fallback_expr: ExprNode


@dataclass
class IteratorNode(ExprNode):
    item_id: str
    item_type: str | None
    iterable_expr: ExprNode
    body: ExprNode
    fallback_expr: ExprNode


@dataclass
class ConditionalNode(ExprNode):
    condition_branchs: list[tuple[ExprNode, ExprNode]]
    fallback_branck: ExprNode


@dataclass
class LetExprNode(ExprNode):
    id: str
    type: str | None
    value: ExprNode
    body: ExprNode


def desugar_let_expr(bindings: list[tuple[str, str | None, ExprNode]], body: ExprNode):
    head, *tail = bindings
    id, type, value = head

    return LetExprNode(
        id, type, value, body if len(tail) == 0 else desugar_let_expr(tail, body)
    )


@dataclass
class FunctionNode(ASTNode):
    id: str
    params: list[tuple[str, str | None]]
    return_type: str | None
    body: ExprNode


@dataclass
class MethodSpecNode(ASTNode):
    id: str
    params: list[tuple[str, str]]
    return_type: str


@dataclass
class ProtocolNode(ASTNode):
    type: str
    extends: list[str]
    method_specs: list[MethodSpecNode]


@dataclass
class TypePropertyNode(ASTNode):
    id: str
    type: str | None
    value: ExprNode


@dataclass
class TypeNode(ASTNode):
    type: str
    params: list[tuple[str, str | None]] | None
    parent_type: str | None
    parent_args: list[ExprNode] | None
    members: list[TypePropertyNode | FunctionNode]


def is_assignable(node: ASTNode):
    is_assignable_id = isinstance(node, IdentifierNode) and (not node.is_builtin)
    return is_assignable_id or isinstance(node, (IndexingNode, MemberAccessingNode))


def get_safe_type(typename: str | None, ctx: Context):
    return ctx.get_type_or_proto(typename) if typename is not None else typename


class SemanticChecker(object):  # TODO implement all the nodes
    def __init__(self):
        self.errors = []

    @visitor.on("node")
    def visit(self, node, scope):
        pass

    @visitor.when(LiteralNode)
    def visit(self, node: LiteralNode, scope: Scope):
        return self.errors

    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, scope: Scope):
        if not scope.is_var_defined(node.value):
            self.errors.append(f"Variable {node.value} not defined")
        return self.errors

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, scope: Scope):
        self.visit(node.target, scope)
        self.visit(node.value, scope)

        if not is_assignable(node.target):
            self.errors.append(f"Expression '' does not support destructive assignment")

        return self.errors


class TypeCollector(object):
    def __init__(self):
        self.errors: list[str] = []

    @visitor.on("node")
    def visit(self, node, context):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, ctx: Context):
        for child in node.declarations:
            if not isinstance(child, FunctionNode):
                self.visit(child, ctx)

        return self.errors

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context):
        try:
            ctx.create_type(node.type)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(ProtocolNode)
    def visit(self, node: TypeNode, ctx: Context):
        try:
            ctx.create_protocol(node.type)
        except SemanticError as se:
            self.errors.append(se.text)


class TypeBuilder(object):
    def __init__(self):
        self.errors: list[str] = []

        # type doesn't include None because current_type will be set before read
        self.current_type: Union[Type, Proto] = None

    @visitor.on("node")
    def visit(self, node, ctx):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, ctx: Context):
        for declaration in node.declarations:
            if not isinstance(declaration, FunctionNode):
                self.visit(declaration, ctx)

        return self.errors

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, ctx: Context):
        try:
            self.current_type = ctx.get_type(node.type)
        except SemanticError as se:
            self.errors.append(se.text)

        if node.parent_type:
            try:
                parent_type = ctx.get_type(node.parent_type)
                self.current_type.set_parent(parent_type)
            except SemanticError as se:
                self.errors.append(se.text)

        if node.params is not None:
            try:
                params = [(n, get_safe_type(t, ctx)) for n, t in node.params]
                self.current_type.set_params(params)
            except SemanticError as se:
                self.errors.append(se.text)

        for member in node.members:
            self.visit(member, ctx)

        # TODO: handle parent args

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, ctx: Context):
        try:
            type = get_safe_type(node.type, ctx)
            self.current_type.define_attribute(node.id, type)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, ctx: Context):
        try:
            params = [(n, get_safe_type(t, ctx)) for n, t in node.params]
            self.current_type.define_method(
                node.id, params, node.body, get_safe_type(node.return_type, ctx)
            )
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(ProtocolNode)
    def visit(self, node: ProtocolNode, ctx: Context):
        try:
            self.current_type = ctx.get_protocol(node.type)
        except SemanticError as se:
            self.errors.append(se.text)

        for method_spec in node.method_specs:
            self.visit(method_spec)

    @visitor.when(MethodSpecNode)
    def visit(self, node: MethodSpecNode, ctx: Context):
        try:
            params = [(n, get_safe_type(t, ctx)) for n, t in node.params]
            self.current_type.add_method_spec(
                node.id, params, get_safe_type(node.return_type, ctx)
            )
        except SemanticError as se:
            self.errors.append(se.text)


class TypeChecker:
    def __init__(self, context, errors=[]):
        self.context: Context = context
        self.current_type: Type = None
        self.current_method = None
        self.errors = errors

    @visitor.on("node")
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, scope=None):
        scope = Scope()
        for declaration in node.declarations:
            self.visit(declaration, scope.create_child())
        self.visit(node.expr, scope.create_child())
        return scope

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, scope: Scope):
        self.current_type = self.context.get_type(node.type)
        if node.parent_type:
            parent_type = self.context.get_type(node.parent_type)
            parent_params_size = len(parent_type.params) if parent_type.params else 0
            node_parent_args_size = len(node.parent_args) if node.parent_args else 0
            if parent_params_size != node_parent_args_size:
                self.errors.append(
                    f"Type {node.parent_type} expects {parent_params_size} arguments but {node_parent_args_size} were given"
                )
            if parent_type.params and node.parent_args:
                for parent_arg, node_arg in zip(parent_type.params, node.parent_args):
                    self.visit(node_arg, scope.create_child())
                    if not self.current_type.conforms_to(parent_arg.type):
                        self.errors.append(
                            f"Cannot convert {self.current_type.name} into {parent_arg.type.name}"
                        )
        for member in node.members:
            self.visit(member, scope.create_child())

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode, scope: Scope):
        self.current_method = self.current_type.get_method(node.id)
        for param in node.params:
            self.visit(param, scope)
        self.visit(node.body, scope.create_child())

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode, scope: Scope):
        self.visit(node.value, scope)

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, scope: Scope):
        for member in node.exprs:
            self.visit(member, scope.create_child())

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, scope: Scope):
        # node.type = self.context.get_type("object").name if not node.type else node.type
        if scope.is_defined(node.id):
            self.errors.append(f"Variable {node.id} already defined")
        self.visit(node.value, scope)
        if node.type:
            node_type = self.context.get_type(node.type)
            if not self.current_type.conforms_to(node_type):
                self.errors.append(
                    f"Cannot convert {self.current_type.name} to {node_type.name}"
                )
        scope.define_variable(node.id, self.current_type)
        self.visit(node.body, scope.create_child())

    @visitor.when(TypeInstancingNode)
    def visit(self, node: TypeInstancingNode, scope: Scope):
        self.current_type = self.context.get_type(node.type)
        node_params_size = len(node.args) if node.args else 0
        current_type_params_size = (
            len(self.current_type.params) if self.current_type.params else 0
        )
        if current_type_params_size != node_params_size:
            self.errors.append(
                f"Type {node.type} expects {current_type_params_size} arguments, but {node_params_size} were given"
            )

        for arg in node.args:
            self.visit(arg, scope.create_child())
            node_type = self.context.get_type(node.type)
            if not node_type.conforms_to(self.current_type):
                self.errors.append(
                    f"Cannot convert {self.current_type.name} to {node_type.name}"
                )
        self.current_type = self.context.get_type(node.type)

    @visitor.when(BooleanNode)
    def visit(self, node: BooleanNode, scope: Scope):
        self.current_type = self.context.get_type("Boolean")
