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

TypeAnnotation %= colon + type_identifier, lambda h, s: s[2], None, None
TypeAnnotation %= GRAMMAR.Epsilon, lambda h, s: None

OptionalSemicolon %= semicolon, None, None
OptionalSemicolon %= GRAMMAR.Epsilon, None

Args %= Expr + MoreArgs, lambda h, s: [s[1], *s[2]], None, None
Args %= GRAMMAR.Epsilon, lambda h, s: []
MoreArgs %= comma + Expr + MoreArgs, lambda h, s: [s[2], *s[3]], None, None, None
MoreArgs %= GRAMMAR.Epsilon, lambda h, s: []

Params %= (
    identifier + TypeAnnotation + MoreParams,
    lambda h, s: [(s[1], s[2]), *s[3]],
    None,
    None,
    None,
)
Params %= GRAMMAR.Epsilon, lambda h, s: []
MoreParams %= (
    comma + identifier + TypeAnnotation + MoreParams,
    lambda h, s: [(s[2], s[3]), *s[4]],
    None,
    None,
    None,
    None,
)
MoreParams %= GRAMMAR.Epsilon, lambda h, s: []

Expr %= (
    let + Binding + MoreBindings + in_k + Expr,
    lambda h, s: ast.desugar_let_expr([s[2], *s[3]], s[5]),
    None,
    None,
    None,
    None,
    None,
)
Expr %= (
    if_k + lparen + Expr + rparen + Expr + ElseBranch,
    lambda h, s: ast.Conditional([(s[3], s[5]), *(s[6][:-1])], s[6][-1]),
    None,
    None,
    None,
    None,
    None,
    None,
)
Expr %= (
    while_k + lparen + Expr + rparen + Expr,
    lambda h, s: ast.Loop(s[3], s[5]),
    None,
    None,
    None,
    None,
    None,
)
Expr %= (
    for_k + lparen + identifier + TypeAnnotation + in_k + Expr + rparen + Expr,
    lambda h, s: ast.Iterator(s[3], s[4], s[6], s[8]),
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
Expr %= BlockExpr, lambda h, s: s[1], None
Expr %= Disj + MoreDisjs, lambda h, s: s[2], None, lambda h, s: s[1]

Binding %= identifier + TypeAnnotation + bind + Expr, None, None, None, None, None
MoreBindings %= (
    comma + Binding + MoreBindings,
    lambda h, s: [s[2], *s[3]],
    None,
    None,
    None,
)
MoreBindings %= GRAMMAR.Epsilon, lambda h, s: []

ElseBranch %= (
    elif_k + lparen + Expr + rparen + Expr + ElseBranch,
    lambda h, s: [(s[3], s[5]), *s[6]],
    None,
    None,
    None,
    None,
    None,
    None,
)
ElseBranch %= else_k + Expr, lambda h, s: [s[2]], None, None

BlockExpr %= (
    lbrace + Stmt + MoreStmts + rbrace,
    lambda h, s: ast.Block([s[2], *s[3]]),
    None,
    None,
    None,
    None,
)

# statements are the same as exprs but end up in semicolon
# if the expression is inline, otherwise the semicolon is optional
Stmt %= (
    let + Binding + MoreBindings + in_k + Stmt,
    lambda h, s: ast.desugar_let_expr([s[2], *s[3]], s[5]),
    None,
    None,
    None,
    None,
    None,
)
Stmt %= (
    if_k + lparen + Expr + rparen + Expr + ElseStmtBranch,
    lambda h, s: ast.Conditional([(s[3], s[5]), *(s[6][:-1])], s[6][-1]),
    None,
    None,
    None,
    None,
    None,
    None,
)
Stmt %= (
    while_k + lparen + Expr + rparen + Stmt,
    lambda h, s: ast.Loop(s[3], s[5]),
    None,
    None,
    None,
    None,
    None,
)
Stmt %= (
    for_k + lparen + identifier + TypeAnnotation + in_k + Expr + rparen + Stmt,
    lambda h, s: ast.Iterator(s[3], s[4], s[6], s[8]),
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
Stmt %= BlockExpr + OptionalSemicolon, lambda h, s: s[1], None, None
Stmt %= Disj + MoreDisjs + semicolon, lambda h, s: s[2], None, lambda h, s: s[1], None

MoreStmts %= Stmt + MoreStmts, lambda h, s: [s[1], *s[2]], None, None
MoreStmts %= GRAMMAR.Epsilon, lambda h, s: []

ElseStmtBranch %= (
    elif_k + lparen + Expr + rparen + Expr + ElseStmtBranch,
    lambda h, s: [(s[3], s[5]), *s[6]],
    None,
    None,
    None,
    None,
    None,
    None,
)
ElseStmtBranch %= else_k + Stmt, lambda h, s: [s[2]], None, None

MoreDisjs %= (
    disj + Disj + MoreDisjs,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Logic(h[0], s[1], s[2]),
)
MoreDisjs %= GRAMMAR.Epsilon, lambda h, s: h[0]

Disj %= Conj + MoreConjs, lambda h, s: s[2], None, lambda h, s: s[1]

MoreConjs %= (
    conj + Conj + MoreConjs,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Logic(h[0], s[1], s[2]),
)
MoreConjs %= GRAMMAR.Epsilon, lambda h, s: h[0]

Conj %= not_t + Conj, lambda h, s: ast.Negation(s[2]), None, None
Conj %= Concat + Comparison, lambda h, s: s[2], None, lambda h, s: s[1]

Comparison %= lt + Concat, lambda h, s: ast.Comparison(h[0], s[1], s[2]), None, None
Comparison %= gt + Concat, lambda h, s: ast.Comparison(h[0], s[1], s[2]), None, None
Comparison %= le + Concat, lambda h, s: ast.Comparison(h[0], s[1], s[2]), None, None
Comparison %= ge + Concat, lambda h, s: ast.Comparison(h[0], s[1], s[2]), None, None
Comparison %= eq + Concat, lambda h, s: ast.Comparison(h[0], s[1], s[2]), None, None
Comparison %= neq + Concat, lambda h, s: ast.Comparison(h[0], s[1], s[2]), None, None
Comparison %= (
    is_k + type_identifier,
    lambda h, s: ast.RuntimeTypeCheking(h[0], s[2]),
    None,
    None,
)
Comparison %= GRAMMAR.Epsilon, lambda h, s: h[0]

Concat %= Arith + MoreAriths, lambda h, s: s[2], None, lambda h, s: s[1]

MoreAriths %= (
    concat + Arith + MoreAriths,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Concatenation(h[0], s[2]),
)
MoreAriths %= (
    concat_space + Arith + MoreAriths,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Concatenation(ast.Concatenation(h[0], ast.String('" "')), s[2]),
)
MoreAriths %= GRAMMAR.Epsilon, lambda h, s: h[0]

Arith %= Term + MoreTerms, lambda h, s: s[2], None, lambda h, s: s[1]

MoreTerms %= (
    plus + Term + MoreTerms,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Arithmetic(h[0], s[1], s[2]),
)
MoreTerms %= (
    minus + Term + MoreTerms,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Arithmetic(h[0], s[1], s[2]),
)
MoreTerms %= GRAMMAR.Epsilon, lambda h, s: h[0]

Term %= Factor + MoreFactors, lambda h, s: s[2], None, lambda h, s: s[1]

MoreFactors %= (
    times + Factor + MoreFactors,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Arithmetic(h[0], s[1], s[2]),
)
MoreFactors %= (
    div + Factor + MoreFactors,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Arithmetic(h[0], s[1], s[2]),
)
MoreFactors %= (
    mod + Factor + MoreFactors,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.Arithmetic(h[0], s[1], s[2]),
)
MoreFactors %= GRAMMAR.Epsilon, lambda h, s: h[0]

Factor %= (
    Base + Powers,
    lambda h, s: s[1] if s[2] == None else ast.Powering(s[1], s[2]),
    None,
    None,
)

Powers %= (
    power + Base + Powers,
    lambda h, s: s[2] if s[3] == None else ast.Powering(s[2], s[3]),
    None,
    None,
    None,
)
Powers %= GRAMMAR.Epsilon, lambda h, s: None

Base %= minus + Base, lambda h, s: ast.ArithmeticNegation(s[2]), None, None
Base %= Molecule + Mutation, lambda h, s: s[2], None, lambda h, s: s[1]

Molecule %= Atom + Action, lambda h, s: s[2], None, lambda h, s: s[1]

Mutation %= as_k + type_identifier, lambda h, s: ast.Downcasting(h[0], s[2]), None, None
Mutation %= mut + Molecule, lambda h, s: ast.Mutation(h[0], s[2]), None, None
Mutation %= GRAMMAR.Epsilon, lambda h, s: h[0]

Atom %= number, lambda h, s: ast.Number(s[1]), None
Atom %= string, lambda h, s: ast.String(s[1]), None
Atom %= true_k, lambda h, s: ast.Boolean(s[1]), None
Atom %= false_k, lambda h, s: ast.Boolean(s[1]), None
Atom %= builtin_identifier, lambda h, s: ast.Identifier(s[1], True), None
Atom %= identifier, lambda h,s: ast.Identifier(s[1]), None
Atom %= (
    new + type_identifier + lparen + Args + rparen,
    lambda h, s: ast.TypeInstanceCreation(s[2], s[4]),
    None,
    None,
    None,
    None,
    None,
)
Atom %= lparen + Expr + rparen, lambda h, s: s[2], None, None, None
Atom %= lbracket + Vector + rbracket, lambda h, s: s[2], None, None, None

Vector %= Expr + VectorStructure, lambda h, s: s[2], None, lambda h, s: s[1]
Vector %= GRAMMAR.Epsilon, None
VectorStructure %= (
    given + identifier + TypeAnnotation + in_k + Expr,
    lambda h, s: ast.MappedIterable(h[0], s[2], s[3], s[5]),
    None,
    None,
    None,
    None,
    None,
)
VectorStructure %= MoreArgs, lambda h, s: ast.Vector([h[0], *s[1]]), None

Action %= (
    dot + identifier + Action,
    lambda h, s: s[3],
    None,
    None,
    lambda h, s: ast.TypeMemberAccessing(h[0], s[2]),
)
Action %= (
    lbracket + number + rbracket + Action,
    lambda h, s: s[4],
    None,
    None,
    None,
    lambda h, s: ast.Indexing(h[0], s[2]),
)
Action %= (
    lparen + Args + rparen + Action,
    lambda h, s: s[4],
    None,
    None,
    None,
    lambda h, s: ast.FunctionCall(h[0], s[2]),
)
Action %= GRAMMAR.Epsilon, lambda h, s: h[0]

Program %= Declarations + Expr + OptionalSemicolon, None, None, None, None

Declarations %= Decl + Declarations, None, None, None
Declarations %= GRAMMAR.Epsilon, None

Decl %= (
    func + identifier + lparen + Params + rparen + TypeAnnotation + FunctionBody,
    lambda h, s: ast.Function(s[2], s[4], s[6], s[7]),
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
Decl %= (
    protocol
    + type_identifier
    + Extension
    + lbrace
    + MoreMethodSpecs
    + rbrace
    + OptionalSemicolon,
    lambda h, s: ast.Protocol(s[2], s[3], s[5]),
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
Decl %= (
    type_k
    + type_identifier
    + OptionalParams
    + Inheritance
    + lbrace
    + Member
    + MoreMembers
    + rbrace
    + OptionalSemicolon,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)

FunctionBody %= then + Stmt, lambda h, s: s[2], None, None
FunctionBody %= BlockExpr + OptionalSemicolon, lambda h, s: s[1], None, None

Extension %= (
    extends + type_identifier + MoreTypeIds,
    lambda h, s: [s[2], *s[3]],
    None,
    None,
    None,
)
Extension %= GRAMMAR.Epsilon, lambda h, s: []
MoreTypeIds %= type_identifier + MoreTypeIds, lambda h, s: [s[1], *s[2]], None, None
MoreTypeIds %= GRAMMAR.Epsilon, lambda h, s: []

MethodSpec %= (
    identifier + lparen + Params + rparen + colon + type_identifier + OptionalSemicolon,
    lambda h, s: ast.MethodSpec(s[1], s[3], s[6]),
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
MoreMethodSpecs %= MethodSpec + MoreMethodSpecs, lambda h, s: [s[1], *s[2]], None, None
MoreMethodSpecs %= GRAMMAR.Epsilon, lambda h, s: []

OptionalParams %= lparen + Params + rparen, None, None, None, None
OptionalParams %= GRAMMAR.Epsilon, None

Inheritance %= inherits + type_identifier + OptionalArgs, None, None, None, None
Inheritance %= GRAMMAR.Epsilon, None

OptionalArgs %= lparen + Args + rparen, None, None, None, None
OptionalArgs %= GRAMMAR.Epsilon, None

Member %= identifier + MemberStructure, None, None, None
MemberStructure %= TypeAnnotation + bind + Stmt, None, None, None, None
MemberStructure %= (
    lparen + Params + rparen + TypeAnnotation + FunctionBody,
    None,
    None,
    None,
    None,
    None,
    None,
)

# endregion
