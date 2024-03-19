from .tools.grammar import Grammar
from . import ast


GRAMMAR = Grammar()

# region TERMINALS

## KEYWORDS
let, in_k = GRAMMAR.add_terminals("let in")
if_k, else_k, elif_k = GRAMMAR.add_terminals("if else elif")
while_k, for_k = GRAMMAR.add_terminals("while for")
func = GRAMMAR.add_terminal("function")
type_k, new, inherits, is_k, as_k = GRAMMAR.add_terminals("type new inherits is as")
protocol, extends = GRAMMAR.add_terminals("protocol extends")
true_k, false_k = GRAMMAR.add_terminals("true false")

# OPERATORS
plus, minus, times, div, mod, power = GRAMMAR.add_terminals("+ - * / % pow")
lt, gt, le, ge, eq, neq = GRAMMAR.add_terminals("< > <= >= == !=")
concat, concat_space = GRAMMAR.add_terminals("@ @@")
conj, disj, not_t = GRAMMAR.add_terminals("& | !")

# PUNCTUATION
lparen, rparen, lbrace, rbrace, lbracket, rbracket = GRAMMAR.add_terminals(
    "( ) { } [ ]"
)
colon, semicolon, dot, comma = GRAMMAR.add_terminals(": ; . ,")
then, given = GRAMMAR.add_terminals("=> ||")
bind, mut = GRAMMAR.add_terminals("= :=")

# STRINGS
number, string, identifier, type_identifier, builtin_identifier = GRAMMAR.add_terminals(
    "number string id type_id builtin_id"
)

# endregion

# region NON TERMINALS

TypeAnnotation, OptionalSemicolon = GRAMMAR.add_non_terminals(
    "type_annotation opt_semicolon"
)
Params, MoreParams, OptionalParams = GRAMMAR.add_non_terminals(
    "params more_params opt_params"
)
Args, MoreArgs, OptionalArgs = GRAMMAR.add_non_terminals("args more_args opt_args")

Program = GRAMMAR.add_non_terminal("program", True)
Decl, Declarations = GRAMMAR.add_non_terminals("decl decls")
FunctionBody = GRAMMAR.add_non_terminal("function_body")
MethodSpec, MoreMethodSpecs, Extension, MoreTypeIds = GRAMMAR.add_non_terminals(
    "method_spec more_method_specs extension more_type_ids"
)
Member, MemberStructure, MoreMembers, Inheritance = GRAMMAR.add_non_terminals(
    "member member_structure more_members inheritance"
)

Expr = GRAMMAR.add_non_terminal("expr")
Binding, MoreBindings = GRAMMAR.add_non_terminals("binding more_bindings")
ElseBranch, ElseStmtBranch = GRAMMAR.add_non_terminals("else_branch else_stmt_branch")
BlockExpr, Stmt, MoreStmts = GRAMMAR.add_non_terminals("block_expr stmt more_stmts")

Disj, MoreDisjs = GRAMMAR.add_non_terminals("disj more_disjs")
Conj, MoreConjs = GRAMMAR.add_non_terminals("conj more_conjs")
Concat, Comparison = GRAMMAR.add_non_terminals("concat comparison")
Arith, MoreAriths = GRAMMAR.add_non_terminals("arith more_ariths")
Term, MoreTerms = GRAMMAR.add_non_terminals("term more_terms")
Factor, MoreFactors = GRAMMAR.add_non_terminals("factor more_factors")
Base, Powers = GRAMMAR.add_non_terminals("base powers")
Molecule, Mutation = GRAMMAR.add_non_terminals("molecule mutation")
Atom, Action = GRAMMAR.add_non_terminals("atom action")
Vector, VectorStructure = GRAMMAR.add_non_terminals("vector vector_structure")

# endregion

# region PRODUCTIONS

Program %= (
    Declarations + Expr + OptionalSemicolon,
    lambda h, s: ast.ProgramNode(s[1], s[2]),
)

Decl %= (
    func + identifier + lparen + Params + rparen + TypeAnnotation + FunctionBody,
    lambda h, s: ast.FunctionNode(s[2], s[4], s[6], s[7]),
)
Decl %= (
    protocol
    + type_identifier
    + Extension
    + lbrace
    + MoreMethodSpecs
    + rbrace
    + OptionalSemicolon,
    lambda h, s: ast.ProtocolNode(s[2], s[3], s[5]),
)
Decl %= (
    type_k
    + type_identifier
    + OptionalParams
    + Inheritance
    + lbrace
    + MoreMembers
    + rbrace
    + OptionalSemicolon,
    lambda h, s: ast.TypeNode(s[2], s[3], s[4][0], s[4][1], s[6]),
)

Declarations %= Decl + Declarations, lambda h, s: [s[1], *s[2]]
Declarations %= GRAMMAR.Epsilon, lambda h, s: []

FunctionBody %= then + Stmt, lambda h, s: s[2]
FunctionBody %= BlockExpr + OptionalSemicolon, lambda h, s: s[1]

Extension %= extends + type_identifier + MoreTypeIds, lambda h, s: [s[2], *s[3]]
Extension %= GRAMMAR.Epsilon, lambda h, s: []
MoreTypeIds %= comma + type_identifier + MoreTypeIds, lambda h, s: [s[2], *s[3]]
MoreTypeIds %= GRAMMAR.Epsilon, lambda h, s: []

MethodSpec %= (
    identifier + lparen + Params + rparen + colon + type_identifier + OptionalSemicolon,
    lambda h, s: ast.MethodSpecNode(s[1], s[3], s[6]),
)
MoreMethodSpecs %= MethodSpec + MoreMethodSpecs, lambda h, s: [s[1], *s[2]]
MoreMethodSpecs %= GRAMMAR.Epsilon, lambda h, s: []

OptionalParams %= lparen + Params + rparen, lambda h, s: s[2]
OptionalParams %= GRAMMAR.Epsilon, lambda h, s: None

Inheritance %= inherits + type_identifier + OptionalArgs, lambda h, s: (s[2], s[3])
Inheritance %= GRAMMAR.Epsilon, lambda h, s: (None, None)

OptionalArgs %= lparen + Args + rparen, lambda h, s: s[2]
OptionalArgs %= GRAMMAR.Epsilon, lambda h, s: None

Member %= identifier + MemberStructure, lambda h, s: s[2], None, lambda h, s: s[1]
MemberStructure %= (
    TypeAnnotation + bind + Stmt,
    lambda h, s: ast.TypePropertyNode(h[0], s[1], s[3]),
)
MemberStructure %= (
    lparen + Params + rparen + TypeAnnotation + FunctionBody,
    lambda h, s: ast.MethodNode(h[0], s[2], s[4], s[5]),
)

MoreMembers %= Member + MoreMembers, lambda h, s: [s[1], *s[2]]
MoreMembers %= GRAMMAR.Epsilon, lambda h, s: []

Expr %= (
    let + Binding + MoreBindings + in_k + Expr,
    lambda h, s: ast.desugar_let_expr([s[2], *s[3]], s[5]),
)
Expr %= (
    if_k + lparen + Expr + rparen + Expr + ElseBranch,
    lambda h, s: ast.ConditionalNode([(s[3], s[5]), *(s[6][:-1])], s[6][-1]),
)
Expr %= while_k + lparen + Expr + rparen + Expr, lambda h, s: ast.LoopNode(s[3], s[5])
Expr %= (
    for_k + lparen + identifier + TypeAnnotation + in_k + Expr + rparen + Expr,
    lambda h, s: ast.IteratorNode(s[3], s[4], s[6], s[8]),
)
Expr %= BlockExpr, lambda h, s: s[1]
Expr %= Disj + MoreDisjs, lambda h, s: s[2], None, lambda h, s: s[1]

OptionalSemicolon %= semicolon, lambda h, s: None
OptionalSemicolon %= GRAMMAR.Epsilon, lambda h, s: None

Binding %= identifier + TypeAnnotation + bind + Expr, lambda h, s: (s[1], s[2], s[4])
MoreBindings %= comma + Binding + MoreBindings, lambda h, s: [s[2], *s[3]]
MoreBindings %= GRAMMAR.Epsilon, lambda h, s: []

ElseBranch %= (
    elif_k + lparen + Expr + rparen + Expr + ElseBranch,
    lambda h, s: [(s[3], s[5]), *s[6]],
)
ElseBranch %= else_k + Expr, lambda h, s: [s[2]]

TypeAnnotation %= colon + type_identifier, lambda h, s: s[2]
TypeAnnotation %= GRAMMAR.Epsilon, lambda h, s: None

BlockExpr %= (
    lbrace + Stmt + MoreStmts + rbrace,
    lambda h, s: ast.BlockNode([s[2], *s[3]]),
)

Disj %= Conj + MoreConjs, lambda h, s: s[2], None, lambda h, s: s[1]

MoreDisjs %= (
    disj + Disj + MoreDisjs,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.LogicOpNode(h[0], s[1], s[2]),
)
MoreDisjs %= GRAMMAR.Epsilon, lambda h, s: h[0]

Conj %= not_t + Conj, lambda h, s: ast.NegOpNode(s[2])
Conj %= Concat + Comparison, lambda h, s: s[2], None, lambda h, s: s[1]

MoreConjs %= (
    conj + Conj + MoreConjs,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.LogicOpNode(h[0], s[1], s[2]),
)
MoreConjs %= GRAMMAR.Epsilon, lambda h, s: h[0]

# statements are the same as exprs but end up in semicolon
# if the expression is inline, otherwise the semicolon is optional
Stmt %= (
    let + Binding + MoreBindings + in_k + Stmt,
    lambda h, s: ast.desugar_let_expr([s[2], *s[3]], s[5]),
)
Stmt %= (
    if_k + lparen + Expr + rparen + Expr + ElseStmtBranch,
    lambda h, s: ast.ConditionalNode([(s[3], s[5]), *(s[6][:-1])], s[6][-1]),
)
Stmt %= while_k + lparen + Expr + rparen + Stmt, lambda h, s: ast.LoopNode(s[3], s[5])
Stmt %= (
    for_k + lparen + identifier + TypeAnnotation + in_k + Expr + rparen + Stmt,
    lambda h, s: ast.IteratorNode(s[3], s[4], s[6], s[8]),
)
Stmt %= BlockExpr + OptionalSemicolon, lambda h, s: s[1]
Stmt %= Disj + MoreDisjs + semicolon, lambda h, s: s[2], None, lambda h, s: s[1]

MoreStmts %= Stmt + MoreStmts, lambda h, s: [s[1], *s[2]]
MoreStmts %= GRAMMAR.Epsilon, lambda h, s: []

Args %= Expr + MoreArgs, lambda h, s: [s[1], *s[2]]
Args %= GRAMMAR.Epsilon, lambda h, s: []
MoreArgs %= comma + Expr + MoreArgs, lambda h, s: [s[2], *s[3]]
MoreArgs %= GRAMMAR.Epsilon, lambda h, s: []

Params %= identifier + TypeAnnotation + MoreParams, lambda h, s: [(s[1], s[2]), *s[3]]
Params %= GRAMMAR.Epsilon, lambda h, s: []
MoreParams %= (
    comma + identifier + TypeAnnotation + MoreParams,
    lambda h, s: [(s[2], s[3]), *s[4]],
)
MoreParams %= GRAMMAR.Epsilon, lambda h, s: []

ElseStmtBranch %= (
    elif_k + lparen + Expr + rparen + Expr + ElseStmtBranch,
    lambda h, s: [(s[3], s[5]), *s[6]],
)
ElseStmtBranch %= else_k + Stmt, lambda h, s: [s[2]]

Comparison %= lt + Concat, lambda h, s: ast.ComparisonOpNode(h[0], s[1], s[2])
Comparison %= gt + Concat, lambda h, s: ast.ComparisonOpNode(h[0], s[1], s[2])
Comparison %= le + Concat, lambda h, s: ast.ComparisonOpNode(h[0], s[1], s[2])
Comparison %= ge + Concat, lambda h, s: ast.ComparisonOpNode(h[0], s[1], s[2])
Comparison %= eq + Concat, lambda h, s: ast.ComparisonOpNode(h[0], s[1], s[2])
Comparison %= neq + Concat, lambda h, s: ast.ComparisonOpNode(h[0], s[1], s[2])
Comparison %= is_k + type_identifier, lambda h, s: ast.TypeMatchingNode(h[0], s[2])
Comparison %= GRAMMAR.Epsilon, lambda h, s: h[0]

Concat %= Arith + MoreAriths, lambda h, s: s[2], None, lambda h, s: s[1]

MoreAriths %= (
    concat + Arith + MoreAriths,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.ConcatOpNode(h[0], s[2]),
)
MoreAriths %= (
    concat_space + Arith + MoreAriths,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.ConcatOpNode(ast.ConcatOpNode(h[0], ast.StringNode('" "')), s[2]),
)
MoreAriths %= GRAMMAR.Epsilon, lambda h, s: h[0]

Arith %= Term + MoreTerms, lambda h, s: s[2], None, lambda h, s: s[1]

MoreTerms %= (
    plus + Term + MoreTerms,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.ArithOpNode(h[0], s[1], s[2]),
)
MoreTerms %= (
    minus + Term + MoreTerms,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.ArithOpNode(h[0], s[1], s[2]),
)
MoreTerms %= GRAMMAR.Epsilon, lambda h, s: h[0]

Term %= Factor + MoreFactors, lambda h, s: s[2], None, lambda h, s: s[1]

MoreFactors %= (
    times + Factor + MoreFactors,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.ArithOpNode(h[0], s[1], s[2]),
)
MoreFactors %= (
    div + Factor + MoreFactors,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.ArithOpNode(h[0], s[1], s[2]),
)
MoreFactors %= (
    mod + Factor + MoreFactors,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.ArithOpNode(h[0], s[1], s[2]),
)
MoreFactors %= GRAMMAR.Epsilon, lambda h, s: h[0]

Factor %= (
    Base + Powers,
    lambda h, s: s[1] if s[2] == None else ast.PowerOpNode(s[1], s[2]),
)

Powers %= (
    power + Base + Powers,
    lambda h, s: s[2] if s[3] == None else ast.PowerOpNode(s[2], s[3]),
)
Powers %= GRAMMAR.Epsilon, lambda h, s: None

Base %= minus + Base, lambda h, s: ast.ArithNegOpNode(s[2])
Base %= Molecule + Mutation, lambda h, s: s[2], None, lambda h, s: s[1]

Molecule %= Atom + Action, lambda h, s: s[2], None, lambda h, s: s[1]

Mutation %= as_k + type_identifier, lambda h, s: ast.DowncastingNode(h[0], s[2])
Mutation %= mut + Molecule, lambda h, s: ast.MutationNode(h[0], s[2])
Mutation %= GRAMMAR.Epsilon, lambda h, s: h[0]

Atom %= number, lambda h, s: ast.NumberNode(s[1])
Atom %= string, lambda h, s: ast.StringNode(s[1])
Atom %= true_k, lambda h, s: ast.BooleanNode(s[1])
Atom %= false_k, lambda h, s: ast.BooleanNode(s[1])
Atom %= builtin_identifier, lambda h, s: ast.IdentifierNode(s[1], True)
Atom %= identifier, lambda h, s: ast.IdentifierNode(s[1])
Atom %= (
    new + type_identifier + lparen + Args + rparen,
    lambda h, s: ast.TypeInstancingNode(s[2], s[4]),
)
Atom %= lparen + Expr + rparen, lambda h, s: s[2]
Atom %= lbracket + Vector + rbracket, lambda h, s: s[2]

Vector %= Expr + VectorStructure, lambda h, s: s[2], None, lambda h, s: s[1]
Vector %= GRAMMAR.Epsilon, lambda h, s: ast.VectorNode([])
VectorStructure %= (
    given + identifier + TypeAnnotation + in_k + Expr,
    lambda h, s: ast.MappedIterableNode(h[0], s[2], s[3], s[5]),
)
VectorStructure %= MoreArgs, lambda h, s: ast.VectorNode([h[0], *s[1]])

Action %= (
    dot + identifier + Action,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.MemberAccessingNode(h[0], s[2]),
)
Action %= (
    lbracket + Expr + rbracket + Action,
    lambda h, s: s[4],
    None,
    None,
    None,
    lambda h, s: ast.IndexingNode(h[0], s[2]),
)
Action %= (
    lparen + Args + rparen + Action,
    lambda h, s: s[4],
    None,
    None,
    None,
    lambda h, s: ast.FunctionCallNode(h[0], s[2]),
)
Action %= GRAMMAR.Epsilon, lambda h, s: h[0]

# endregion
