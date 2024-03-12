from dataclasses import dataclass

from .tools.semantic import AST


@dataclass
class Number(AST):
    value: str


@dataclass
class String(AST):
    value: str


@dataclass
class Boolean(AST):
    value: str


@dataclass
class Identifier(AST):
    value: str
    is_builtin: bool = False
