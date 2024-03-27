from .tools.lexer import create_lexer, keyword_row
from .tools.semantic.context import Context
from .tools.semantic.scope import Scope
from . import grammar as g
from . import types as t


lexer = create_lexer(
    [
        keyword_row(g.let),
        keyword_row(g.in_k),
        keyword_row(g.if_k),
        keyword_row(g.else_k),
        keyword_row(g.elif_k),
        keyword_row(g.for_k),
        keyword_row(g.func),
        keyword_row(g.type_k),
        keyword_row(g.new),
        keyword_row(g.inherits),
        keyword_row(g.is_k),
        keyword_row(g.as_k),
        keyword_row(g.protocol),
        keyword_row(g.extends),
        keyword_row(g.true_k),
        keyword_row(g.false_k),
        keyword_row(g.plus),
        (g.minus, r"\-"),
        (g.times, r"\*"),
        keyword_row(g.div),
        keyword_row(g.mod),
        (g.power, r"\*\*|^"),
        keyword_row(g.lt),
        keyword_row(g.gt),
        keyword_row(g.le),
        keyword_row(g.ge),
        keyword_row(g.eq),
        keyword_row(g.neq),
        keyword_row(g.concat),
        keyword_row(g.concat_space),
        keyword_row(g.conj),
        (g.disj, r"\|"),
        keyword_row(g.not_t),
        (g.lparen, r"\("),
        (g.rparen, r"\)"),
        keyword_row(g.lbrace),
        keyword_row(g.rbrace),
        keyword_row(g.lbracket),
        keyword_row(g.rbracket),
        keyword_row(g.colon),
        keyword_row(g.semicolon),
        keyword_row(g.dot),
        keyword_row(g.comma),
        keyword_row(g.then),
        (g.given, r"\|\|"),
        keyword_row(g.bind),
        keyword_row(g.mut),
        (g.builtin_identifier, r"E|PI|base|print|range|sqrt|exp|log|rand|sin|cos"),
        (g.type_identifier, r"A-Z(a-z|A-Z|0-9|_)*"),
        (g.identifier, r"(a-z|_)(a-z|A-Z|0-9|_)*"),
        (g.number, r"(0|1-90-9*)(.0-90-9*)?"),
        (g.string, '"(\\"|\x00-!|#-\x7f)*"'),
        (None, r" *"),
        (None, "\n*"),
    ],
    g.GRAMMAR.EOF,
)


context = Context(
    [t.OBJECT_TYPE, t.FUNCTION_TYPE, t.NUMBER_TYPE, t.STRING_TYPE, t.BOOLEAN_TYPE],
    [t.ITERABLE_PROTO],
)

scope = Scope()
scope.define_constant("E", t.NUMBER_TYPE)
scope.define_constant("PI", t.NUMBER_TYPE)
scope.define_function("print", [("obj", t.OBJECT_TYPE)], t.OBJECT_TYPE)
scope.define_function(
    "range",
    [("min", t.NUMBER_TYPE), ("max", t.NUMBER_TYPE)],
    t.VectorType(t.NUMBER_TYPE),
)
scope.define_function("sqrt", [("value", t.NUMBER_TYPE)], t.NUMBER_TYPE)
scope.define_function("exp", [("value", t.NUMBER_TYPE)], t.NUMBER_TYPE)
scope.define_function(
    "log", [("base", t.NUMBER_TYPE), ("value", t.NUMBER_TYPE)], t.NUMBER_TYPE
)
scope.define_function("rand", [], t.NUMBER_TYPE)
scope.define_function("sin", [("angle", t.NUMBER_TYPE)], t.NUMBER_TYPE)
scope.define_function("cos", [("angle", t.NUMBER_TYPE)], t.NUMBER_TYPE)
