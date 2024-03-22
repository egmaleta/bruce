from dataclasses import dataclass

from .tools.semantic import ASTNode, SemanticError
from .tools.semantic.context import Context, Type
from .tools.semantic.scope import Scope
from .tools import visitor


class ExprNode(ASTNode):
    pass


@dataclass
class ProgramNode(ASTNode):
    declarations: list[ASTNode]
    expr: ExprNode


@dataclass
class LiteralNode(ExprNode):
    value: str


class NumberNode(LiteralNode):
    pass


@dataclass
class StringNode(LiteralNode):
    def __post_init__(self):
        self.value = self.value[1:-1]


class BooleanNode(LiteralNode):
    pass


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


@dataclass
class IteratorNode(ExprNode):
    item_id: str
    item_type: str | None
    iterable_expr: ExprNode
    body: ExprNode


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
        id, type, value, body if len(
            tail) == 0 else desugar_let_expr(tail, body)
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
    params: list[tuple[str, str | None]]
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
    is_assignable_id = isinstance(
        node, IdentifierNode) and (not node.is_builtin)
    return is_assignable_id or isinstance(node, (IndexingNode, MemberAccessingNode))


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
            self.errors.append(
                f"Expression '' does not support destructive assignment")

        return self.errors


class TypeCollector(object):
    def __init__(self):
        self.errors = []

    @visitor.on("node")
    def visit(self, node, context):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode, ctx: Context):
        for child in node.declarations:
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
    def __init__(self, context, errors=[]):
        self.context: Context = context
        self.errors: list[str] = errors
        self.current_type: Type = None

    @visitor.on("node")
    def visit(self, node):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode):
        for declaration in node.declarations:
            self.visit(declaration)

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode):
        self.current_type = self.context.get_type(node.type)
        if node.parent_type:
            try:
                parent_type = self.context.get_type(node.parent_type)
                self.current_type.set_parent(parent_type)
            except SemanticError as se:
                self.errors.append(se.text)

        if node.params:
            try:
                self.current_type.set_params(node.params)
            except SemanticError as se:
                self.errors.append(se.text)

        for member in node.members:
            self.visit(member)

    @visitor.when(TypePropertyNode)
    def visit(self, node: TypePropertyNode):
        try:
            self.current_type.define_attribute(node.id, node.type)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(FunctionNode)
    def visit(self, node: FunctionNode):
        try:
            params_name = [param[0] for param in node.params]
            params_type = [param[1] for param in node.params]
            self.current_type.define_method(
                node.id, params_name, params_type, node.return_type)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(ProtocolNode)
    def visit(self, node: ProtocolNode):
        try:
            self.current_type = self.context.get_protocol(node.type)
            for method_spec in node.method_specs:
                self.visit(method_spec)
        except SemanticError as se:
            self.errors.append(se.text)

    @visitor.when(MethodSpecNode)
    def visit(self, node: MethodSpecNode):
        try:
            params_name = [param[0] for param in node.params]
            params_type = [param[1] for param in node.params]
            self.current_type.define_method(
                node.id, params_name, params_type, node.return_type)
        except SemanticError as se:
            self.errors.append(se.text)


class TypeChecker:
    def __init__(self, context, errors=[]):
        self.context = context
        self.current_type = None
        self.current_method = None
        self.errors = errors

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node, scope=None):
        scope = Scope()
        for declaration in node.declarations:
            self.visit(declaration, scope.create_child())
        return scope

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, scope: Scope):
        self.current_type = self.context.get_type(node.type)
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

    @visitor.when(LetExprNode)
    def visit(self, node: LetExprNode, scope: Scope):
        if scope.is_var_defined(node.id):
            self.errors.append(f"Variable {node.id} already defined")
        self.visit(node.value, scope)
        scope.define_var(node.id, node.type)
        self.visit(node.body, scope.create_child())
