from .tools.lexer import create_lexer


# region Tokenizer

nonzero_digits = "|".join(str(n) for n in range(1, 10))
letters = "|".join(chr(n) for n in range(ord("a"), ord("z") + 1))
capital_letters = "|".join(chr(n) for n in range(ord("A"), ord("Z") + 1))

lexer = create_lexer(
    [
        ("number", f"({nonzero_digits})(0|{nonzero_digits})*"),
        ("for", "for"),
        ("foreach", "foreach"),
        ("let", "let"),
        ("in", "in"),
        ("if", "if"),
        ("else", "else"),
        ("elif", "elif"),
        ("while", "while"),
        ("function", "function"),
        ("type", "type"),
        ("new", "new"),
        ("inherits", "inherits"),
        ("is", "is"),
        ("as", "as"),
        ("protocol", "protocol"),
        ("extends", "extends"),
        ("true", "true"),
        ("false", "false"),
        ("plus", "\\+"),
        ("minus", "-"),
        ("star", "\\*"),
        ("div", "/"),
        ("mod", "%"),
        ("power", "\\^"),
        ("power_alt", "\\*\\*"),
        ("lt", "<"),
        ("gt", ">"),
        ("le", "<="),
        ("ge", ">="),
        ("eq", "=="),
        ("neq", "!="),
        ("concat", "@"),
        ("concat_space", "@@"),
        ("conj", "&"),
        ("disj", "\\|"),
        ("not", "!"),
        ("lparen", "\\("),
        ("rparen", "\\)"),
        ("lbrace", "\\{"),
        ("rbrace", "\\}"),
        ("lbracket", "\\["),
        ("rbracket", "\\]"),
        ("colon", ":"),
        ("semicolon", ";"),
        ("dot", "\\."),
        ("comma", ","),
        ("then", "=>"),
        ("given", "\\|\\|"),
        ("bind", "="),
        ("mut", ":="),
        ("space", "  *"),
    ],
    "eof",
)

# endregion
