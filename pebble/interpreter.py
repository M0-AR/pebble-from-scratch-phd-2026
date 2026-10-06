"""Stage 4 — Statements + program runner (memory = environment dict).

Statements:
    let NAME = expression     store value under name
    print expression          append value to outputs

`run_program` walks lines in order, threading one shared env, exactly like
the transcript's price/count/total walk-through.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .errors import PebbleError
from .evaluator import Env, evaluate
from .parser import Node, Parser
from .tokens import Token, tokenize_line


@dataclass
class LetStmt:
    name: str
    expr: Node
    line: int


@dataclass
class PrintStmt:
    expr: Node
    line: int


Statement = LetStmt | PrintStmt


def parse_statement(tokens: List[Token], raw_line: str = "") -> Statement:
    p = Parser(tokens)
    first = p.peek()
    if first.kind == "KEYWORD" and first.value == "let":
        p.advance()
        name_tok = p.take("NAME")
        p.take("OP", "=")
        expr = p.expression()
        end = p.peek()
        if end.kind != "EOF":
            raise PebbleError(
                f"Unexpected {end.value!r} after expression", end.line, end.col
            )
        return LetStmt(name_tok.value, expr, first.line)
    if first.kind == "KEYWORD" and first.value == "print":
        p.advance()
        expr = p.expression()
        end = p.peek()
        if end.kind != "EOF":
            raise PebbleError(
                f"Unexpected {end.value!r} after expression", end.line, end.col
            )
        return PrintStmt(expr, first.line)
    if first.kind == "EOF":
        raise PebbleError("Empty statement", first.line, first.col)
    raise PebbleError(
        f"Expected 'let' or 'print' but found {first.value!r}", first.line, first.col
    )


def execute(stmt: Statement, env: Env) -> int | None:
    if isinstance(stmt, LetStmt):
        env[stmt.name] = evaluate(stmt.expr, env)
        return None
    return evaluate(stmt.expr, env)


def run_program(source: str) -> Tuple[List[int], Env]:
    """Run a whole program line-by-line. Returns (printed outputs, env)."""
    outputs: List[int] = []
    env: Env = {}
    lines = source.splitlines() or [""]
    for idx, raw in enumerate(lines, start=1):
        if raw.strip() == "":
            continue
        tokens = tokenize_line(raw, idx)
        try:
            stmt = parse_statement(tokens, raw)
        except PebbleError as e:
            # attach source line for caret rendering upstream
            raise PebbleError(e.message, e.line, e.col) from None
        try:
            value = execute(stmt, env)
        except PebbleError as e:
            raise PebbleError(e.message, stmt.line, e.col) from None
        if value is not None:
            outputs.append(value)
    return outputs, env


def run_file(path: str) -> Tuple[List[int], Env]:
    with open(path, encoding="utf-8") as f:
        return run_program(f.read())
