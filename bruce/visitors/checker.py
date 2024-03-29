from ..tools.semantic.scope import Scope
from ..tools import visitor
from ..ast import *

Context = []

class SemanticChecker(object):  # TODO implement all the nodes
    def __init__(self, context = None):
        self.errors = []
        self.context = context

    @visitor.on("node")
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode) # falta ver que no esten def cosas con el mismo nombre y eso
    def visit(self,node:ProgramNode,scope:Scope):
        program_scope = scope.create_child()
        for declaration in node.declarations:
            self.visit(declaration,program_scope)
        self.visit(node.expr,program_scope)    

        return self.errors    


    @visitor.when(IdentifierNode)
    def visit(self, node: IdentifierNode, scope: Scope):
        if not scope.is_var_defined(node.value):
            self.errors.append(f"Variable {node.value} not defined")
    
        
    
    @visitor.when(FunctionCallNode)
    def visit(self, node:FunctionCallNode, scope:Scope):
        if not scope.is_func_defined(node.target.value):
           # print(node.target.value)
            self.errors.append(f"Function {node.target} not defined")
    
        for arg in node.args:
            self.visit(arg,scope)    
    

    @visitor.when(FunctionNode)
    def visit(self, node:FunctionNode, scope:Scope):
        if not scope.is_func_defined(node.id):
            scope.define_function(node.id,node.params)
        else:
            self.errors.append(f"Function {node.id} alredy defined. Cannot define more than one function with the same name")    

        func_scope = scope.create_child()

        for param in node.params:
            func_scope.define_variable(param[0])

        # body es un BlockNode o  una expresion
        self.visit(node.body,func_scope)


    @visitor.when(BlockNode)
    def visit(self,node:BlockNode, scope:Scope):
        my_scope = scope.create_child()
        for expr in node.exprs:
            self.visit(expr, my_scope.create_child())


    @visitor.when(BinaryOpNode)
    def visit(self, node:BinaryOpNode,scope:Scope):
        self.visit(node.left,scope)
        self.visit(node.right,scope)
    

    @visitor.when(MutationNode)
    def visit(self, node: MutationNode, scope: Scope):
        my_scope = scope.create_child()
        self.visit(node.target, my_scope.create_child())
        self.visit(node.value, my_scope.create_child())

        if not is_assignable(node.target):
            self.errors.append(f"Expression '' does not support destructive assignment")


    @visitor.when(LetExprNode)
    def visit(self,node:LetExprNode, scope:Scope):
        scope.define_variable(node.id)
        self.visit(node.value,scope)
        let_scope = scope.create_child()
        self.visit(node.body,let_scope)

    @visitor.when(ConditionalNode)
    def visit(self, node:ConditionalNode, scope:Scope):
        my_scope = scope.create_child()

        for branch in node.condition_branchs:
            self.visit(branch[0],my_scope)
            self.visit(branch[1],my_scope)

        self.visit(node.fallback_branch, my_scope) 

    @visitor.when(LoopNode)
    def visit(self, node:LoopNode, scope:Scope):
        my_scope = scope.create_child()

        self.visit(node.condition,my_scope)
        self.visit(node.body,my_scope)
        self.visit(node.fallback_expr,my_scope)

    @visitor.when(UnaryOpNode)
    def visit(self, node:UnaryOpNode, scope: Scope):
        my_scope = scope.create_child()
        self.visit(node.operand,my_scope)


        

    @visitor.when(TypeNode)
    def visit(self, node: TypeNode, scope:Scope):
        my_scope = scope.create_child()

        for param in node.params:
            my_scope.define_variable(param[0])

        for expr in node.parent_args:
            self.visit(expr, my_scope)

        for member in node.members:
            self.visit(member,my_scope)      

    @visitor.when(TypePropertyNode)
    def visit(self, node:TypePropertyNode, scope:Scope):
        my_scope = scope.create_child()

        self.visit(node.value, my_scope)

    
    @visitor.when(TypeInstancingNode)
    def visit(self,node: TypeInstancingNode, scope:Scope):
        if not node.type in self.context:
            self.errors.append(f"Type {node.type} does not exist in the current context")

        my_scope = scope.create_child()

        for arg in node.args:
            self.visit(arg,my_scope)    

    @visitor.when(TypeMatchingNode)
    def visit(self, node: TypeMatchingNode, scope: Scope):
        my_scope = scope.create_child()
        self.visit(node.target)        
        

    @visitor.when(VectorNode)
    def visit(self, node:VectorNode, scope:Scope):
        my_context = scope.create_child()

        for expr in node.items:
            self.visit(expr, my_context)

    @visitor.when(MappedIterableNode)
    def visit(self, node: MappedIterableNode, scope: Scope):
        my_context = scope.create_child() 

        pass       

    @visitor.when(MemberAccessingNode)
    def visit(self, node:MemberAccessingNode, scope:Scope):
        my_scope = scope.create_child()

        self.visit(node.target, my_scope)

    @visitor.when(DowncastingNode)
    def visit(self, node:DowncastingNode,scope:Scope):
        my_scope = scope.create_child()
        self.visit(node.target, my_scope)

    @visitor.when(MethodSpecNode)
    def visit(self,node:MethodSpecNode, scope:Scope):
        pass
  
    @visitor.when(ProtocolNode)
    def visit(self,node:ProtocolNode, scope:Scope):
        pass







