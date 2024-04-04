from math import pi, e

from .tools.lexer import create_lexer, keyword_row
from .tools.semantic.context import Context
from .tools.semantic.scope import Scope
from . import grammar as g
from . import types as t
from . import names as n

from .grammar import GRAMMAR
from .tools.parser import UnexpectedToken, create_parser, evaluate_parse
from .visitors.desugarer import Desugarer
from .visitors.type_builder import TypeCollector, TypeBuilder
from .visitors.function_collector import FunctionCollector
from .visitors.checker import SemanticChecker
from .visitors.type_inferer import TypeInferer
from .visitors.type_checker import TypeChecker
from .visitors.evaluator import Evaluator


lexer = create_lexer(
    [
        keyword_row(g.let),
        keyword_row(g.in_k),
        keyword_row(g.if_k),
        keyword_row(g.else_k),
        keyword_row(g.elif_k),
        keyword_row(g.for_k),
        keyword_row(g.while_k),
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
        (
            g.builtin_identifier,
            "|".join(
                [
                    n.E_CONST_NAME,
                    n.PI_CONST_NAME,
                    n.BASE_FUNC_NAME,
                    n.PRINT_FUNC_NAME,
                    n.RANGE_FUNC_NAME,
                    n.SQRT_FUNC_NAME,
                    n.EXP_FUNC_NAME,
                    n.LOG_FUNC_NAME,
                    n.RAND_FUNC_NAME,
                    n.SIN_FUNC_NAME,
                    n.COS_FUNC_NAME,
                ]
            ),
        ),
        (g.type_identifier, r"A-Z(a-z|A-Z|0-9|_)*"),
        (g.identifier, r"(a-z|_)(a-z|A-Z|0-9|_)*"),
        (g.number, r"(0|1-90-9*)(.0-90-9*)?"),
        (g.string, '"(\\\\"|\x00-!|#-\x7f)*"'),
        (None, " *"),
        (None, "\n*"),
        (None, "\r*"),
        (None, "\r\n*"),
        (None, "\t*"),
        (None, "//(\x00-\t|\x0b-\x7f)*"),
    ],
    g.GRAMMAR.EOF,
)


context = Context(
    [t.OBJECT_TYPE, t.NUMBER_TYPE, t.STRING_TYPE, t.BOOLEAN_TYPE],
    [t.ITERABLE_PROTO],
)

scope = Scope()
scope.define_constant(n.E_CONST_NAME, t.NUMBER_TYPE, (e, t.NUMBER_TYPE))
scope.define_constant(n.PI_CONST_NAME, t.NUMBER_TYPE, (pi, t.NUMBER_TYPE))
scope.define_function(n.PRINT_FUNC_NAME, [("obj", t.OBJECT_TYPE)], t.OBJECT_TYPE)
scope.define_function(
    n.RANGE_FUNC_NAME,
    [("min", t.NUMBER_TYPE), ("max", t.NUMBER_TYPE)],
    t.VectorType(t.NUMBER_TYPE),
)
scope.define_function(n.SQRT_FUNC_NAME, [("value", t.NUMBER_TYPE)], t.NUMBER_TYPE)
scope.define_function(n.EXP_FUNC_NAME, [("value", t.NUMBER_TYPE)], t.NUMBER_TYPE)
scope.define_function(
    n.LOG_FUNC_NAME, [("base", t.NUMBER_TYPE), ("value", t.NUMBER_TYPE)], t.NUMBER_TYPE
)
scope.define_function(n.RAND_FUNC_NAME, [], t.NUMBER_TYPE)
scope.define_function(n.SIN_FUNC_NAME, [("angle", t.NUMBER_TYPE)], t.NUMBER_TYPE)
scope.define_function(n.COS_FUNC_NAME, [("angle", t.NUMBER_TYPE)], t.NUMBER_TYPE)


def pipeline(program: str):
    tokens = lexer(program)
    parser = create_parser(GRAMMAR)
    try:
        left_parse = parser(tokens)
    except UnexpectedToken as e:
        print(e)
        return
    ast = evaluate_parse(left_parse, tokens)
    des = Desugarer()
    ast = des.visit(ast)

    tc = TypeCollector()
    errors = tc.visit(ast, context)
    if len(errors) > 0:
        print(f"Type Collector: \n{errors}")
        return
    tb = TypeBuilder(errors)
    errors = tb.visit(ast, context)
    if len(errors) > 0:
        print(f"Type Builder: \n{errors}")
        return
    fc = FunctionCollector()
    errors = fc.visit(ast, context, scope)
    if len(errors) > 0:
        print(f"Function Collector: \n {errors}")
        return
    sc = SemanticChecker()
    errors = sc.visit(ast, context, scope)
    if len(errors) > 0:
        print(f"Semantic Checker: \n {errors}")
        return
    inf = TypeInferer()
    errors = inf.visit(ast, context, scope)
    if len(errors) > 0:
        print(f"Type Inferer: \n {errors}")
        return
    tc = TypeChecker(errors)
    tc.visit(ast, context, scope)
    if len(errors) > 0:
        print(f"Type Checker: \n{errors}")
        return
    ev = Evaluator()
    ev.visit(ast, context, scope)
