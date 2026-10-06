"""Stage 2 — Parser: tokens -> syntax tree (recursive descent).

Grammar (one method per rule; call chain encodes precedence):
    expression := term (('+' | '-') term)*        # lowest, left-assoc
    term       := factor (('*' | '/' | '%') factor)*  # tighter, left-assoc
    factor     := NUMBER | NAME | '(' expression ')'

Why this shape (research consensus: Loyola guide, Crenshaw, Crafting
Interpreters, CPython PEG notes):
- Lower-precedence rule calls the tighter rule for operands, so tighter
  operators land deeper in the tree and evaluate first.
- `while` loop over same-level operators => left associativity:
  2-3-4 parses as (2-3)-4 = -5, not 2-(3-4).
- factor -> '(' expression ')' is mutual recursion back to the top,
  so brackets override precedence: (2+3)*4 puts '+' below '*'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from .errors import PebbleError
from .tokens import Token


@dataclass
class Number:
    value: int
    line: int = 1
    col: int = 1


@dataclass
class Var:
    name: str
    line: int = 1
    col: int = 1


@dataclass
class BinOp:
    op: str
    left: "Node"
    right: "Node"


Node = Union[Number, Var, BinOp]


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # -- cursor helpers -------------------------------------------------
    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def take(self, kind: str, value: str = "") -> Token:
        """Consume expected token or raise with its line/col (the `take`)."""
        tok = self.peek()
        if tok.kind != kind or (value and tok.value != value):
            if value:
                want = f"{value!r}"
            else:
                want = kind.lower()
            if tok.kind == "EOF":
                found = "the end of the line"
            else:
                found = f"{tok.value!r}"
            raise PebbleError(f"Expected {want}, but found {found}", tok.line, tok.col)
        return self.advance()

    # -- grammar --------------------------------------------------------
    def expression(self) -> Node:
        node = self.term()
        while self.peek().kind == "OP" and self.peek().value in ("+", "-"):
            op = self.advance().value
            rhs = self.term()
            node = BinOp(op, node, rhs)
        return node

    def term(self) -> Node:
        node = self.factor()
        while self.peek().kind == "OP" and self.peek().value in ("*", "/", "%"):
            op = self.advance().value
            rhs = self.factor()
            node = BinOp(op, node, rhs)
        return node

    def factor(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.advance()
            return Number(int(tok.value), tok.line, tok.col)
        if tok.kind == "NAME":
            self.advance()
            return Var(tok.value, tok.line, tok.col)
        if tok.kind == "OP" and tok.value == "(":
            self.advance()
            node = self.expression()
            self.take("OP", ")")  # error here mentions "')'" + position
            return node
        if tok.kind == "EOF":
            raise PebbleError(
                "Expected a number, name, or '(' but found the end of the line",
                tok.line,
                tok.col,
            )
        raise PebbleError(
            f"Expected a number, name, or '(' but found {tok.value!r}",
            tok.line,
            tok.col,
        )

    def parse_expression(self) -> Node:
        node = self.expression()
        tok = self.peek()
        if tok.kind != "EOF":
            raise PebbleError(
                f"Unexpected {tok.value!r} after expression", tok.line, tok.col
            )
        return node


def parse_expression_tokens(tokens: List[Token]) -> Node:
    return Parser(tokens).parse_expression()


def tree_string(node: Node) -> str:
    """S-expression for tests/traces: (+ 2 (* 3 4))."""
    if isinstance(node, Number):
        return str(node.value)
    if isinstance(node, Var):
        return node.name
    return f"({node.op} {tree_string(node.left)} {tree_string(node.right)})"
