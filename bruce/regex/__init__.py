from ..parser import Grammar, evaluate_parse, create_parser
from .ast import UnionNode, ConcatNode, ClosureNode, SymbolNode, EpsilonNode
from ..utils import Token
from .automata import nfa_to_dfa 

G = Grammar()

E = G.NonTerminal('E', True)
T, F, A, X, Y, Z = G.NonTerminals('T F A X Y Z')
pipe, star, opar, cpar, symbol, epsilon = G.Terminals('| * ( ) symbol ε')

############################ BEGIN PRODUCTIONS ############################
# ======================================================================= #
#                                                                         #
# ========================== { E --> T X } ============================== #
#                                                                         #
E %= T + X, lambda h,s: s[2], None, lambda h,s: s[1]
#                                                                         #
# =================== { X --> '|' T X | epsilon } ======================= #
#                                                                         #
X %= pipe + T + X, lambda h,s: s[3], None, None, lambda h,s: UnionNode(h[0], s[2])
X %= G.Epsilon, lambda h,s: h[0]
#                                                                         #
# ============================ { T --> F Y } ============================ #
#                                                                         #
T %= F + Y, lambda h,s: s[2], None, lambda h,s: s[1]
#                                                                         #
# ==================== { Y --> F Y | epsilon } ========================== #
#                                                                         #
Y %=  F + Y, lambda h,s: s[2], None, lambda h,s: ConcatNode(h[0], s[1])
Y %= G.Epsilon, lambda h,s: h[0]
#                                                                         #
# ======================= { F --> A Z } ================================= #
#                                                                         #
F %= A + Z, lambda h,s: s[2], None, lambda h,s: s[1]
#                                                                         #
# ==================== { Z --> * Z | epsilon } ========================== #
#                                                                         #
Z %= star + Z, lambda h,s: s[2], None, lambda h,s: ClosureNode(h[0]) 
Z %= G.Epsilon, lambda h,s: h[0]
#                                                                         #
# ==================== { A --> symbol | 'Epsilon' | ( E ) } ============= #
#                                                                         #
# ==================== { A --> symbol | 'Epsilon' | ( E ) } ============= #
#                                                                         #
A %= symbol, lambda h,s: SymbolNode(s[1]), symbol
A %= epsilon, lambda h,s: EpsilonNode(s[1]), epsilon
A %= opar + E + cpar, lambda h,s: s[2], None, None, None
#                                                                         #
# ======================================================================= #
############################# END PRODUCTIONS #############################

def regex_tokenizer(text, G, skip_whitespaces=True):
    tokens = []
    # > fixed_tokens = ???
    fixed_tokens = "| * ( ) ε".split()

    for char in text:
        if skip_whitespaces and char.isspace():
            continue
        elif char in fixed_tokens:
            tokens.append(Token(char,G.symbDict[char]))
        else:
            tokens.append(Token(char,G.symbDict["symbol"]))
        
    tokens.append(Token('$', G.EOF))
    return tokens

class Regex:
    def __init__(self, text):
        tokens = regex_tokenizer(text, Grammar)
        parser = create_parser(Grammar)
        left_parser = parser(tokens)
        ast = evaluate_parse(left_parser, tokens)
        nfa = ast.evaluate()
        self.automaton = nfa_to_dfa(nfa)
