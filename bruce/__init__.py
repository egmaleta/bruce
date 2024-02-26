from .grammar import Grammar


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
plus, minus, times, div, mod, power, power_alt = GRAMMAR.add_terminals("+ - * / % ^ **")
lt, gt, le, ge, eq, neq = GRAMMAR.add_terminals("< > <= >= == !=")
concat, concat_space = GRAMMAR.add_terminals("@ @@")
conj, disj, not_t = GRAMMAR.add_terminals("& | !")

# PUNCTUATION
lparen, rparen, lbrace, rbrace, lbracket, rbracket = GRAMMAR.add_terminals(
    "( ) { } [ ]"
)
colon, semicolon, dot, comma = GRAMMAR.add_terminals(": ; . ,")
then = GRAMMAR.add_terminal("=>")
bind, mut = GRAMMAR.add_terminals("= :=")

# STRINGS
number, string, identifier, type_identifier = GRAMMAR.add_terminals(
    "number string id type_id"
)

# endregion

# region NON TERMINALS

TypeAnnotation = GRAMMAR.add_non_terminal("type_annotation")
Expr = GRAMMAR.add_non_terminal("expr", True)
LetExpr = GRAMMAR.add_non_terminal("let_expr")
BranchExpr, ElseBlock = GRAMMAR.add_non_terminals("if_expr else_block")
LoopExpr = GRAMMAR.add_non_terminal("loop_expr")
BlockExpr, MoreExprs = GRAMMAR.add_non_terminals("block_expr more_exprs")
Disj, MoreDisjs = GRAMMAR.add_non_terminals("disj more_disjs")
Conj, MoreConjs = GRAMMAR.add_non_terminals("conj more_conjs")
Comparison, Comparer = GRAMMAR.add_non_terminals("comparison comparer")
Arith = GRAMMAR.add_non_terminal("arith")
Term, MoreTerms = GRAMMAR.add_non_terminals("term more_terms")
Factor, MoreFactors = GRAMMAR.add_non_terminals("factor more_factors")
Base, Powers = GRAMMAR.add_non_terminals("base powers")
Args, MoreArgs = GRAMMAR.add_non_terminals("args more_args")
Atom, Action = GRAMMAR.add_non_terminals("atom action")

# endregion

# region PRODUCTIONS

TypeAnnotation %= colon + type_identifier, None, None, None
TypeAnnotation %= GRAMMAR.Epsilon, None

Expr %= LetExpr, None, None
Expr %= BranchExpr, None, None
Expr %= LoopExpr, None, None
Expr %= BlockExpr, None, None
Expr %= Disj + MoreDisjs, None, None, None

LetExpr %= (
    let + identifier + TypeAnnotation + bind + Expr + in_k + Expr,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)

BranchExpr %= (
    if_k + lparen + Expr + rparen + Expr + ElseBlock,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
ElseBlock %= (
    elif_k + lparen + Expr + rparen + Expr + ElseBlock,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
ElseBlock %= else_k + Expr, None, None, None

LoopExpr %= while_k + lparen + Expr + rparen + Expr, None, None, None, None, None, None
LoopExpr %= (
    for_k + lparen + identifier + in_k + Expr + rparen + Expr,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)

BlockExpr %= lbrace + Expr + MoreExprs + rbrace, None, None, None, None, None
MoreExprs %= semicolon + Expr + MoreExprs, None, None, None, None
MoreExprs %= GRAMMAR.Epsilon, None

MoreDisjs %= disj + Disj + MoreDisjs, None, None, None, None
MoreDisjs %= GRAMMAR.Epsilon, None

Disj %= Conj + MoreConjs, None, None, None

MoreConjs %= conj + Conj + MoreConjs, None, None, None, None
MoreConjs %= GRAMMAR.Epsilon, None

Conj %= not_t + Conj, None, None, None
Conj %= Comparison, None, None

Comparison %= Arith + Comparer + Arith, None, None, None, None
Comparison %= Arith + is_k + type_identifier, None, None, None, None

Comparer %= lt, None, None
Comparer %= gt, None, None
Comparer %= le, None, None
Comparer %= ge, None, None
Comparer %= eq, None, None
Comparer %= neq, None, None

Arith %= Term + MoreTerms, None, None, None

MoreTerms %= plus + Term + MoreTerms, None, None, None, None
MoreTerms %= minus + Term + MoreTerms, None, None, None, None
MoreTerms %= concat + Term + MoreTerms, None, None, None, None
MoreTerms %= concat_space + Term + MoreTerms, None, None, None, None
MoreTerms %= GRAMMAR.Epsilon, None

Term %= Factor + MoreFactors, None, None, None

MoreFactors %= times + Factor + MoreFactors, None, None, None, None
MoreFactors %= div + Factor + MoreFactors, None, None, None, None
MoreFactors %= mod + Factor + MoreFactors, None, None, None, None
MoreFactors %= GRAMMAR.Epsilon, None

Factor %= minus + Factor, None, None, None
Factor %= Base + Powers, None, None, None

Powers %= power + Factor, None, None, None
Powers %= power_alt + Factor, None, None, None
Powers %= GRAMMAR.Epsilon, None

Base %= Atom + Action, None, None, None

Atom %= number, None
Atom %= string, None
Atom %= true_k, None
Atom %= false_k, None
Atom %= identifier, None
Atom %= lbracket + Args + rbracket, None, None, None, None
Atom %= (
    new + type_identifier + lparen + Args + rparen,
    None,
    None,
    None,
    None,
    None,
    None,
)
Atom %= lparen + Expr + rparen, None, None, None, None

Args %= Expr + MoreArgs, None, None, None
Args %= GRAMMAR.Epsilon, None
MoreArgs %= comma + Expr + MoreArgs, None, None, None, None
MoreArgs %= GRAMMAR.Epsilon, None

Action %= dot + identifier + Action, None, None, None, None
Action %= lbracket + number + rbracket + Action, None, None, None, None, None
Action %= lparen + Args + rparen + Action, None, None, None, None, None
Action %= GRAMMAR.Epsilon, None

# endregion

# TODO: 'as' expr, mut expr
