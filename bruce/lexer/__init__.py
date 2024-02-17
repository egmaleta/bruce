from re import Pattern

from grammar import Terminal


class Token:
    def __init__(self, lexeme: str, type: Terminal):
        self.lexeme = lexeme
        self.type = type


def _match(prefix: Pattern | str, code: str):
    if isinstance(prefix, str):
        return prefix if code.startswith(prefix) else None

    match = prefix.match(code)
    return match.string if match != None else None


def create_lexer(
    prefixes: list[tuple[Pattern | str, Terminal]],
    ignored_prefixes: list[Pattern | str],
):
    all_prefixes: list[tuple[Pattern | str, Terminal | None]] = prefixes + [
        (pattern, None) for pattern in ignored_prefixes
    ]

    def lexer(code: str):
        tokens = []

        i = 0
        while i < len(code):
            rest_of_code = code[i:]

            for prefix, type in all_prefixes:
                lexeme = _match(prefix, rest_of_code)
                if lexeme != None:
                    i += len(lexeme)
                    if type != None:
                        tokens.append(Token(lexeme, type))
                    break
            else:
                # raise error
                pass

        return tokens

    return lexer
