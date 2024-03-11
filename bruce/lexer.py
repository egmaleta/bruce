from .token import Token
from .regex.automata import State
from .regex import Regex


class Lexer:
    def __init__(self, table, eof):
        self.eof = eof
        self.regexs = self._build_regexs(table)
        self.automaton = self._build_automaton()

    def _build_regexs(self, table):
        regexs = []
        for n, (token_type, regex) in enumerate(table):
            r = Regex(regex)
            automata = r.automaton
            start_state, states = State.from_nfa(automata, get_states=True)
            for state in automata.finals:
                states[state].tag = (token_type, n)
            regexs.append(start_state)
        return regexs

    def _build_automaton(self):
        start = State("start")
        for state in self.regexs:
            start.add_epsilon_transition(state)
        return start.to_deterministic()

    def _walk(self, string):
        state = self.automaton
        final = state if state.final else None
        final_lex = lex = ""

        for symbol in string:
            lex += symbol
            if symbol in state.transitions:
                state = state.transitions[symbol][0]
                if state.final:
                    max_priority = len(self.regexs)
                    for s in state.state:
                        if s.final and s.tag[1] < max_priority:
                            final = s.tag[0]
                            max_priority = s.tag[1]
                    final_lex = lex
            else:
                break

        return final, final_lex

    def _tokenize(self, text):
        index = 0

        while index < len(text):
            final, lex = self._walk(text[index:])
            index += len(lex)
            yield lex, final

        yield "$", self.eof

    def __call__(self, text):
        return [Token(lex, ttype) for lex, ttype in self._tokenize(text)]

def create_lexer(table, eof):
    l = Lexer(table, eof)
    return lambda text: l(text)
