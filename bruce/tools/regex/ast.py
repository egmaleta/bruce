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
