from ..grammar import Grammar
from ..parser import evaluate_parse, create_parser
from ..token import Token
from .ast import UnionNode, ConcatNode, ClosureNode, SymbolNode, EpsilonNode
from .automata import nfa_to_dfa

G = Grammar()

E = G.add_non_terminal("E", True)
T, F, A, X, Y, Z = G.add_non_terminals("T F A X Y Z")
pipe, star, opar, cpar, symbol, epsilon = G.add_terminals("| * ( ) symbol ε")

############################ BEGIN PRODUCTIONS ############################
# ======================================================================= #
#                                                                         #
# ========================== { E --> T X } ============================== #
#                                                                         #
E %= T + X, lambda h, s: s[2], None, lambda h, s: s[1]
#                                                                         #
# =================== { X --> '|' T X | epsilon } ======================= #
#                                                                         #
X %= pipe + T + X, lambda h, s: s[3], None, None, lambda h, s: UnionNode(h[0], s[2])
X %= G.Epsilon, lambda h, s: h[0]
#                                                                         #
# ============================ { T --> F Y } ============================ #
#                                                                         #
T %= F + Y, lambda h, s: s[2], None, lambda h, s: s[1]
#                                                                         #
# ==================== { Y --> F Y | epsilon } ========================== #
#                                                                         #
Y %= F + Y, lambda h, s: s[2], None, lambda h, s: ConcatNode(h[0], s[1])
Y %= G.Epsilon, lambda h, s: h[0]
#                                                                         #
# ======================= { F --> A Z } ================================= #
#                                                                         #
F %= A + Z, lambda h, s: s[2], None, lambda h, s: s[1]
#                                                                         #
# ==================== { Z --> * Z | epsilon } ========================== #
#                                                                         #
Z %= star + Z, lambda h, s: s[2], None, lambda h, s: ClosureNode(h[0])
Z %= G.Epsilon, lambda h, s: h[0]
#                                                                         #
# ==================== { A --> symbol | 'Epsilon' | ( E ) } ============= #
#                                                                         #
# ==================== { A --> symbol | 'Epsilon' | ( E ) } ============= #
#                                                                         #
A %= symbol, lambda h, s: SymbolNode(s[1]), symbol
A %= epsilon, lambda h, s: EpsilonNode(s[1]), epsilon
A %= opar + E + cpar, lambda h, s: s[2], None, None, None
#                                                                         #
# ======================================================================= #
############################# END PRODUCTIONS #############################


def regex_tokenizer(text, G, skip_whitespaces=True):
    tokens = []
    fixed_tokens = "| * ( ) ε".split()

    for char in text:
        if skip_whitespaces and char.isspace():
            continue
        elif char in fixed_tokens:
            tokens.append(Token(char, G.symbol_dict[char]))
        else:
            tokens.append(Token(char, G.symbol_dict["symbol"]))

    tokens.append(Token("$", G.EOF))
    return tokens


class Regex:
    def __init__(self, text):
        tokens = regex_tokenizer(text, G, False)
        parser = create_parser(G)
        left_parser = parser([token.token_type for token in tokens])
        ast = evaluate_parse(left_parser, tokens)
        nfa = ast.evaluate()
        self.automaton = nfa_to_dfa(nfa)

    def __call__(self, text: str):
        return self.automaton.recognize(text)
