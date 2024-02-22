from ..grammar.utils import Grammar, NonTerminal, Terminal, Production, Symbol
from .utils import ContainerSet, compute_firsts, compute_follows, build_parsing_table


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
