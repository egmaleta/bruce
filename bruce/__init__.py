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

# OPERATORS
plus, minus, times, div, mod, power, power_alt = GRAMMAR.add_terminals("+ - * / % ^ **")
lt, gt, le, ge, eq, neq = GRAMMAR.add_terminals("< > <= >= == !=")
concat, concat_space = GRAMMAR.add_terminals("@ @@")
conj, disj, neg = GRAMMAR.add_terminals("& | !")

# PUNCTUATION
lparen, rparen, lbrace, rbrace, lbracket, rbracket = GRAMMAR.add_terminals(
    "( ) { } [ ]"
)
colon, semicolon, dot, comma = GRAMMAR.add_terminals(": ; . ,")
then = GRAMMAR.add_terminal("=>")
bind, mut = GRAMMAR.add_terminals("= :=")

# STRINGS
number, string, identifier = GRAMMAR.add_terminals("number string id")

# endregion

# region NON TERMINALS

Expr = GRAMMAR.add_non_terminal("expr", True)
LetExpr = GRAMMAR.add_non_terminal("let_expr")
BranchExpr, ElseBlock = GRAMMAR.add_non_terminals("if_expr else_block")
Disj, MoreDisjs = GRAMMAR.add_non_terminals("disj more_disjs")
Conj, MoreConjs = GRAMMAR.add_non_terminals("conj more_conjs")
Comp = GRAMMAR.add_non_terminal("comp")

# endregion

# region PRODUCTIONS

LetExpr %= (
    let + identifier + bind + Expr + in_k + Expr,
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

Expr %= LetExpr, None, None
Expr %= BranchExpr, None, None
Expr %= Disj + MoreDisjs, None, None, None

MoreDisjs %= disj + Disj + MoreDisjs, None, None, None, None
MoreDisjs %= GRAMMAR.Epsilon, None

Disj %= Conj + MoreConjs, None, None, None

MoreConjs %= conj + Conj + MoreConjs, None, None, None, None
MoreConjs %= GRAMMAR.Epsilon, None

Conj %= neg + Conj, None, None, None
Conj %= Comp, None, None

# endregion
