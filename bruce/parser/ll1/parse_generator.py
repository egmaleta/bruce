from utils import ContainerSet, Symbol, NonTerminal,Terminal, EOF, Sentence, SentenceList, Epsilon, Production,Grammar


#Firsts

# Computes First(alpha), given First(Vt) and First(Vn) 
# alpha in (Vt U Vn)*
def compute_local_first(firsts, alpha):
    first_alpha = ContainerSet()
    
    try:
        alpha_is_epsilon = alpha.IsEpsilon
    except:
        alpha_is_epsilon = False
    
    ###################################################
    # alpha == epsilon ? First(alpha) = { epsilon }
    ###################################################
    #                   <CODE_HERE>                   #
    ###################################################
    if alpha_is_epsilon:
        first_alpha.set_epsilon()
    ###################################################
    # alpha = X1 ... XN
    # First(Xi) subconjunto First(alpha)
    # epsilon pertenece a First(X1)...First(Xi) ? First(Xi+1) subconjunto de First(X) y First(alpha)
    # epsilon pertenece a First(X1)...First(XN) ? epsilon pertence a First(X) y al First(alpha)
    ###################################################
    #                   <CODE_HERE>                   #
    ###################################################
    else:
        first_alpha.update(firsts[alpha[0]])
        e = firsts[alpha[0]].contains_epsilon

        for sy in alpha[1:]:
            if e:
                first_alpha.update(firsts[sy])
                e = firsts[sy].contains_epsilon
            else:
                break
            
        if e:
            first_alpha.set_epsilon()

    # First(alpha)
    return first_alpha


# Computes First(Vt) U First(Vn) U First(alpha)
# P: X -> alpha
def compute_firsts(G):
    firsts = {}
    change = True
    
    # init First(Vt)
    for terminal in G.terminals:
        firsts[terminal] = ContainerSet(terminal)
        
    # init First(Vn)
    for nonterminal in G.nonTerminals:
        firsts[nonterminal] = ContainerSet()
    
    while change:
        change = False
        
        # P: X -> alpha
        for production in G.Productions:
            X = production.Left
            alpha = production.Right
            
            # get current First(X)
            first_X = firsts[X]
                
            # init First(alpha)
            try:
                first_alpha = firsts[alpha]
            except KeyError:
                first_alpha = firsts[alpha] = ContainerSet()
            
            # CurrentFirst(alpha)???
            local_first = compute_local_first(firsts, alpha)
            
            # update First(X) and First(alpha) from CurrentFirst(alpha)
            change |= first_alpha.hard_update(local_first)
            change |= first_X.hard_update(local_first)
                    
    # First(Vt) + First(Vt) + First(RightSides)
    return firsts



# Follows

from itertools import islice


def compute_follows(G, firsts):
    follows = { }
    change = True
    
    local_firsts = {}
    
    # init Follow(Vn)
    for nonterminal in G.nonTerminals:
        follows[nonterminal] = ContainerSet()
    follows[G.startSymbol] = ContainerSet(G.EOF)
    
    while change:
        change = False
        
        # P: X -> alpha
        for production in G.Productions:
            X = production.Left
            alpha = production.Right
            
            follow_X = follows[X]
            
            ###################################################
            # X -> zeta Y beta
            # First(beta) - { epsilon } subset of Follow(Y)
            # beta ->* epsilon or X -> zeta Y ? Follow(X) subset of Follow(Y)
            ###################################################
            #                   <CODE_HERE>                   #
            ###################################################
            l = len(alpha)
            for k, Y in enumerate(alpha, 1):
                if Y.IsNonTerminal:
                    beta = Sentence(*islice(alpha, k, l)) if k < l else None

                    if beta:
                        if beta not in local_firsts:
                            local_firsts[beta] = compute_local_first(firsts, beta)
                        
                        fb = local_firsts[beta]
                        change |= follows[Y].update(fb)

                        if fb.contains_epsilon:
                            change |= follows[Y].update(follow_X)
                    else:
                        change |= follows[Y].update(follow_X)
    
    # Follow(Vn)
    return follows


# Tabla LL1    

def build_parsing_table(G, firsts, follows):
    # init parsing table
    M = {}
    
    # P: X -> alpha
    for production in G.Productions:
        X = production.Left
        alpha = production.Right
        
        ###################################################
        # working with symbols on First(alpha) ...
        ###################################################
        #                   <CODE_HERE>                   #
        ###################################################
        for terminal in firsts[alpha]:
            if (X, terminal) in M:
                M[X, terminal].append(production)
            else:
                M[X, terminal] = [production]
        
        ###################################################
        # working with epsilon...
        ###################################################
        #                   <CODE_HERE>                   #
        ###################################################
        if firsts[alpha].contains_epsilon:
            for terminal in follows[X]:
                if (X, terminal) in M:
                    M[X, terminal].append(production)
                else:
                    M[X, terminal] = [production]
    
    # parsing table is ready!!!
    return M            


def metodo_predictivo_no_recursivo(G, M=None, firsts=None, follows=None):
    
    # checking table...
    if M is None:
        if firsts is None:
            firsts = compute_firsts(G)
        if follows is None:
            follows = compute_follows(G, firsts)
        M = build_parsing_table(G, firsts, follows)
    
    
    # parser construction...
    def parser(w):
        
        ###################################################
        # w ends with $ (G.EOF)
        ###################################################
        # init:
        ### stack =  ????
        ### cursor = ????
        ### output = ????
        ###################################################
        cursor = 0
        p = M[G.startSymbol, w[cursor]][0]
        output = [p]
        stack = [*reversed(p.Right)]
        
        # parsing w...
        while True:
            top = stack.pop()
            a = w[cursor]
            
            ###################################################
            #                   <CODE_HERE>                   #
            ###################################################
            if top.IsNonTerminal:
                p = M[top, a][0]
                output.append(p)
                if not p.IsEpsilon:
                    stack.extend(reversed(p.Right))
            else:
                if isinstance(top, EOF):
                    break
                if top == a:
                    cursor += 1
                else:
                    raise Exception('Parsing Error: Malformed Expression!')
            
            if not stack:
                break


        # left parse is ready!!!
        return output
    
    # parser is ready!!!
    return parser
        