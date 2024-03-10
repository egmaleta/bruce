from itertools import islice

from .grammar import Symbol, Sentence, Grammar, NonTerminal, Terminal, Production, EOF


class ContainerSet:
    def __init__(self, *values: Symbol, contains_epsilon=False):
        self.set = set(values)
        self.contains_epsilon = contains_epsilon

    def add(self, value: Symbol):
        n = len(self.set)
        self.set.add(value)
        return n != len(self.set)

    def set_epsilon(self, value=True):
        last = self.contains_epsilon
        self.contains_epsilon = value
        return last != self.contains_epsilon

    def update(self, other: set[Symbol]):
        n = len(self.set)
        self.set.update(other.set)
        return n != len(self.set)

    def epsilon_update(self, other: set[Symbol]):
        return self.set_epsilon(self.contains_epsilon | other.contains_epsilon)

    def hard_update(self, other: set[Symbol]):
        return self.update(other) | self.epsilon_update(other)

    def __len__(self):
        return len(self.set) + int(self.contains_epsilon)

    def __str__(self):
        return "%s-%s" % (str(self.set), self.contains_epsilon)

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.set)

    def __eq__(self, other):
        return (
            isinstance(other, ContainerSet)
            and self.set == other.set
            and self.contains_epsilon == other.contains_epsilon
        )


def compute_local_first(firsts: dict[Symbol, ContainerSet], alpha: Sentence):
    first_alpha = ContainerSet()

    try:
        alpha_is_epsilon = alpha.is_epsilon
    except:
        alpha_is_epsilon = False

    if alpha_is_epsilon:
        first_alpha.set_epsilon()
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

    return first_alpha


def compute_firsts(G: Grammar):
    firsts: dict[Symbol, ContainerSet] = {}
    change = True

    for terminal in G.terminals:
        firsts[terminal] = ContainerSet(terminal)

    for nonterminal in G.non_terminals:
        firsts[nonterminal] = ContainerSet()

    while change:
        change = False

        for production in G.productions:
            X = production.left
            alpha = production.right

            first_X = firsts[X]

            # try:
            #     first_alpha = firsts[alpha]
            # except KeyError:
            #     first_alpha = firsts[alpha] = ContainerSet()
            if alpha not in firsts:
                firsts[alpha] = ContainerSet()
            first_alpha = firsts[alpha]

            local_first = compute_local_first(firsts, alpha)

            change |= first_alpha.hard_update(local_first)
            change |= first_X.hard_update(local_first)

    return firsts


def compute_follows(G: Grammar, firsts: dict[Symbol, ContainerSet]):
    follows: dict[NonTerminal, ContainerSet] = {}
    change = True

    local_firsts: dict[Sentence, ContainerSet] = {}

    for nonterminal in G.non_terminals:
        follows[nonterminal] = ContainerSet()
    follows[G.start_symbol] = ContainerSet(G.EOF)

    while change:
        change = False

        for production in G.productions:
            X = production.left
            alpha = production.right

            follow_X = follows[X]

            l = len(alpha)
            for k, Y in enumerate(alpha, 1):
                if Y.is_non_terminal:
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

    return follows


def build_parsing_table(
    G: Grammar,
    firsts: dict[Symbol, ContainerSet],
    follows: dict[NonTerminal, ContainerSet],
):
    M: dict[tuple[NonTerminal, Terminal], Production] = {}

    for production in G.productions:
        X = production.left
        alpha = production.right

        for terminal in firsts[alpha]:
            if (X, terminal) in M:
                M[X, terminal].append(production)
            else:
                M[X, terminal] = [production]

        if firsts[alpha].contains_epsilon:
            for terminal in follows[X]:
                if (X, terminal) in M:
                    M[X, terminal].append(production)
                else:
                    M[X, terminal] = [production]

    return M


def create_parser(
    G: Grammar,
    M: dict[tuple[NonTerminal, Terminal], Production] | None = None,
    firsts: dict[Symbol, ContainerSet] | None = None,
    follows: dict[NonTerminal, ContainerSet] | None = None,
):
    if M is None:
        if firsts is None:
            firsts = compute_firsts(G)
        if follows is None:
            follows = compute_follows(G, firsts)
        M = build_parsing_table(G, firsts, follows)

    def parser(token_types: list[Terminal]):
        cursor = 0
        p = M[G.start_symbol, token_types[cursor]][0]
        output = [p]
        stack = [*reversed(p.right)]

        while True:
            top = stack.pop()
            a = token_types[cursor]

            if top.is_non_terminal:
                p = M[top, a][0]
                output.append(p)
                if not p.is_epsilon:
                    stack.extend(reversed(p.right))
            else:
                if isinstance(top, G.EOF):
                    break
                if top == a:
                    cursor += 1
                else:
                    # TODO: use our own errors
                    raise Exception("Parsing Error: Malformed Expression!")

            if not stack:
                break

        return output

    return parser


def evaluate_parse(left_parse, tokens):
    if not left_parse or not tokens:
        return

    left_parse = iter(left_parse)
    tokens = iter(tokens)
    result = evaluate(next(left_parse), left_parse, tokens)

    assert isinstance(next(tokens).token_type, EOF)
    return result


def evaluate(production, left_parse, tokens, inherited_value=None):
    head, body = production
    attributes = production.attributes

    # Insert your code here ...
    # > synteticed = ...
    # > inherited = ...
    # Anything to do with inherited_value?
    synteticed = [None] * (len(body) + 1)
    inherited = [None] * (len(body) + 1)

    inherited[0] = inherited_value

    for i, symbol in enumerate(body, 1):
        if symbol.IsTerminal:
            assert inherited[i] is None
            # Insert your code here ...
            token = next(tokens)
            if token.token_type == "num":
                synteticed[i] = float(token.lex)
            else:
                synteticed[i] = token.lex
        else:
            next_production = next(left_parse)
            assert symbol == next_production.Left
            # Insert your code here ...
            if not attributes[i] is None:
                inherited[i] = attributes[i](inherited, synteticed)
            synteticed[i] = evaluate(next_production, left_parse, tokens, inherited[i])

    return attributes[0](inherited, synteticed)
