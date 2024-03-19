from .automata import NFA, DFA, nfa_to_dfa
from .automata import (
    automata_union,
    automata_concatenation,
    automata_closure,
    automata_minimization,
)

EPSILON = "ε"


class Node:
    def evaluate(self):
        raise NotImplementedError()


class AtomicNode(Node):
    def __init__(self, symbol):
        self.lex = symbol


class UnaryNode(Node):
    def __init__(self, node):
        self.node = node

    def evaluate(self):
        value = self.node.evaluate()
        return self.operate(value)

    @staticmethod
    def operate(value):
        raise NotImplementedError()


class BinaryNode(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self):
        lvalue = self.left.evaluate()
        rvalue = self.right.evaluate()
        return self.operate(lvalue, rvalue)

    @staticmethod
    def operate(lvalue, rvalue):
        raise NotImplementedError()


class EpsilonNode(Node):
    def evaluate(self):
        return NFA(1, [0], {})


class SymbolNode(AtomicNode):
    def evaluate(self):
        s = self.lex
        return NFA(2, [1], {(0, s): [1]})


class ClosureNode(UnaryNode):
    @staticmethod
    def operate(value):
        return automata_closure(value)


class UnionNode(BinaryNode):
    @staticmethod
    def operate(lvalue, rvalue):
        return automata_union(lvalue, rvalue)


class ConcatNode(BinaryNode):
    @staticmethod
    def operate(lvalue, rvalue):
        return automata_concatenation(lvalue, rvalue)


class RangeNode(Node):
    LETTERS = "abcdefghijklmnñopqrstuvwxyz"
    CAPITAL_LETTERS = LETTERS.upper()
    DIGITS = "0123456789"

    @staticmethod
    def _range_from(target: str, lower: str, upper: str):
        try:
            li = target.index(lower)
            ui = target.index(upper)
        except:
            return None
        else:
            if ui < li:
                return None

            return target[li : ui + 1]

    def __init__(self, lower, upper):
        self.lower: str = lower
        self.upper: str = upper

    def evaluate(self):
        r = lambda target: self._range_from(target, self.lower, self.upper)
        chars: str | None = None

        if self.lower.isdigit() and self.upper.isdigit():
            chars = r(self.DIGITS)
        elif self.lower.isalpha() and self.upper.isalpha():
            if self.lower.isupper() and self.upper.isupper():
                chars = r(self.CAPITAL_LETTERS)
            else:
                chars = r(self.LETTERS)

        if chars == None:
            raise Exception(f"Invalid range: {(self.lower, self.upper)}")

        node = SymbolNode(chars[0])
        for ch in chars[1:]:
            node = UnionNode(node, SymbolNode(ch))

        return node.evaluate()
