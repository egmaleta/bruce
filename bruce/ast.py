from dataclasses import dataclass

from .tools.semantic import AST


@dataclass
class Number(AST):
    value: str
