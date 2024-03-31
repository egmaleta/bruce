class Symbol:
    def __init__(self, name: str, grammar: "Grammar"):
        self.name = name
        self.grammar = grammar

    @property
    def is_terminal(self):
        return False

    @property
    def is_non_terminal(self):
        return False

    @property
    def is_epsilon(self):
        return False

    def __add__(self, other):
        if isinstance(other, Symbol):
            return Sentence(self, other)

        raise TypeError(other)

    def __or__(self, other):
        if isinstance(other, Sentence):
            return SentenceList(Sentence(self), other)

        raise TypeError(other)

    def __len__(self):
        return 1

    def __str__(self):
        return self.name

    def __repr__(self):
        return repr(self.name)


class NonTerminal(Symbol):
    def __init__(self, name: str, grammar: "Grammar"):
        super().__init__(name, grammar)
        self.productions: list["Production"] = []

    @property
    def is_non_terminal(self):
        return True

    def __imod__(self, other):
        if isinstance(other, tuple):
            s: Sentence | Symbol = other[0]
            attrs = other[1:]

            # the number of attributes `len(attrs)` must be equal
            # to the length of the production body plus one (the head) `len(s) + 1`
            diff = len(s) + 1 - len(attrs)
            if diff > 0:
                attrs += (None,) * diff

            assert len(attrs) == len(s) + 1, "Too many attributes"

            p = Production(self, s, attrs)
            self.grammar.add_production(p)

            return self

        if isinstance(other, (Symbol, Sentence)):
            attrs = (None,) * (len(other) + 1)

            p = Production(self, other, attrs)
            self.grammar.add_production(p)

            return self

        raise TypeError(other)


class Terminal(Symbol):
    @property
    def is_terminal(self):
        return True


class EOF(Terminal):
    def __init__(self, grammar: "Grammar"):
        super().__init__("$", grammar)


class Sentence:
    def __init__(self, *args: Symbol):
        self.symbols = tuple(x for x in args if not x.is_epsilon)
        self.hash = hash(self.symbols)

    @property
    def is_epsilon(self):
        return False

    def __add__(self, other):
        if isinstance(other, Symbol):
            return Sentence(*(self.symbols + (other,)))

        if isinstance(other, Sentence):
            return Sentence(*(self.symbols + other.symbols))

        raise TypeError(other)

    def __or__(self, other):
        if isinstance(other, Sentence):
            return SentenceList(self, other)

        if isinstance(other, Symbol):
            return SentenceList(self, Sentence(other))

        raise TypeError(other)

    def __iter__(self):
        return iter(self.symbols)

    def __getitem__(self, index):
        return self.symbols[index]

    def __eq__(self, other):
        return self.symbols == other.symbols

    def __hash__(self):
        return self.hash

    def __len__(self):
        return len(self.symbols)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return ("%s " * len(self.symbols) % tuple(self.symbols)).strip()


class SentenceList:
    def __init__(self, *args: Sentence):
        self.sentences = list(args)

    def add(self, symbol: Symbol | Sentence | None):
        if not symbol and (symbol is None or not symbol.is_epsilon):
            raise ValueError(symbol)

        self.sentences.append(symbol)

    def __iter__(self):
        return iter(self.sentences)

    def __or__(self, other):
        if isinstance(other, Sentence):
            self.add(other)
            return self

        if isinstance(other, Symbol):
            return self | Sentence(other)


class Epsilon(Terminal, Sentence):
    def __init__(self, grammar: "Grammar"):
        super().__init__("epsilon", grammar)

    @property
    def is_epsilon(self):
        return True

    def __iter__(self):
        yield from ()

    def __add__(self, other):
        return other

    def __eq__(self, other):
        return isinstance(other, Epsilon)

    def __hash__(self):
        return hash("")

    def __len__(self):
        return 0

    def __str__(self):
        return "e"

    def __repr__(self):
        return "epsilon"


class Production:
    def __init__(
        self, nt: NonTerminal, sentence_or_symbol: Sentence | Symbol, attributes
    ):
        sentence = (
            sentence_or_symbol
            if isinstance(sentence_or_symbol, Sentence)
            else Sentence(sentence_or_symbol)
        )

        self.left = nt
        self.right = sentence
        self.attributes = attributes

    @property
    def is_epsilon(self):
        return self.right.is_epsilon

    def __iter__(self):
        yield self.left
        yield self.right

    def __eq__(self, other):
        return (
            isinstance(other, Production)
            and self.left == other.left
            and self.right == other.right
        )

    def __hash__(self):
        return hash((self.left, self.right))

    def __str__(self):
        return "%s := %s" % (self.left, self.right)

    def __repr__(self):
        return "%s -> %s" % (self.left, self.right)


class Grammar:
    def __init__(self):
        self.productions: list[Production] = []
        self.non_terminals: list[NonTerminal] = []
        self.terminals: list[Terminal] = []
        self.start_symbol: Symbol | None = None

        self.Epsilon = Epsilon(self)
        self.EOF = EOF(self)

        self.symbol_dict: dict[str, Symbol] = {self.EOF.name: self.EOF}

    def add_non_terminal(self, name: str, is_start_symbol=False):
        name = name.strip()
        if not name:
            raise Exception("Empty name")

        nt = NonTerminal(name, self)

        if is_start_symbol:
            if self.start_symbol is None:
                self.start_symbol = nt
            else:
                raise Exception("Cannot define more than one start symbol.")

        self.non_terminals.append(nt)
        self.symbol_dict[name] = nt
        return nt

    def add_non_terminals(self, names: list[str] | str):
        if isinstance(names, str):
            names = names.strip().split()

        return tuple(self.add_non_terminal(name) for name in names)

    def add_production(self, production: Production):
        production.left.productions.append(production)
        self.productions.append(production)

    def add_terminal(self, name: str):
        name = name.strip()
        if not name:
            raise Exception("Empty name")

        t = Terminal(name, self)
        self.terminals.append(t)
        self.symbol_dict[name] = t
        return t

    def add_terminals(self, names: list[str] | str):
        if isinstance(names, str):
            names = names.strip().split()

        return tuple(self.add_terminal(name) for name in names)

    def __getitem__(self, name: str):
        return self.symbol_dict.get(name)

    def __str__(self):
        mul = "%s, "
        ans = "Non-Terminals:\n\t"
        nonterminals = mul * (len(self.non_terminals) - 1) + "%s\n"
        ans += nonterminals % tuple(self.non_terminals)
        ans += "Terminals:\n\t"
        terminals = mul * (len(self.terminals) - 1) + "%s\n"
        ans += terminals % tuple(self.terminals)
        ans += "Productions:\n\t"
        ans += str(self.productions)

        return ans
