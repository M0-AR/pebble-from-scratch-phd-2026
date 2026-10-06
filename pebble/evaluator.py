"""Stage 3 — Evaluator: tree -> value (structural recursion).

Rule: to evaluate an operator, evaluate left, then right, then combine.
The deepest operation therefore runs first — exactly what the tree promises.
Example: (+ 2 (* 3 4)): 3*4=12 climbs, then 2+12=14 exits the top.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .errors import PebbleError
from .parser import BinOp, Node, Number, Var

Env = Dict[str, int]


def evaluate(node: Node, env: Env) -> int:
    if isinstance(node, Number):
        return node.value
    if isinstance(node, Var):
        if node.name not in env:
            raise PebbleError(f"Undefined name {node.name!r}", node.line, node.col)
        return env[node.name]
    if isinstance(node, BinOp):
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            if right == 0:
                raise PebbleError("Division by zero", _col_of(node), _line_of(node))
            return left // right if _is_exact(left, right) else _trunc_div(left, right)
        if node.op == "%":
            if right == 0:
                raise PebbleError("Remainder by zero", _col_of(node), _line_of(node))
            return left % right
        raise PebbleError(f"Unknown operator {node.op!r}", _line_of(node), _col_of(node))
    raise PebbleError("Unknown syntax tree node", 1, 1)


def _line_of(node: BinOp) -> int:
    for child in (node.left, node.right):
        if isinstance(child, (Number, Var)):
            return child.line
    return 1


def _col_of(node: BinOp) -> int:
    for child in (node.left, node.right):
        if isinstance(child, (Number, Var)):
            return child.col
    return 1


def _is_exact(left: int, right: int) -> bool:
    return right != 0 and left % right == 0


def _trunc_div(left: int, right: int) -> int:
    # Pebble uses truncating integer division (C-like), documented + tested.
    # Python // floors; int(/) truncates toward zero.
    return int(left / right)


def evaluate_with_steps(node: Node, env: Env) -> Tuple[int, List[str]]:
    """Evaluate + record one line per operation, deepest-first (for trace)."""
    steps: List[str] = []

    def rec(n: Node) -> int:
        if isinstance(n, Number):
            return n.value
        if isinstance(n, Var):
            if n.name not in env:
                raise PebbleError(f"Undefined name {n.name!r}", n.line, n.col)
            return env[n.name]
        assert isinstance(n, BinOp)
        lval = rec(n.left)
        rval = rec(n.right)
        if n.op == "+":
            out = lval + rval
        elif n.op == "-":
            out = lval - rval
        elif n.op == "*":
            out = lval * rval
        elif n.op == "/":
            if rval == 0:
                raise PebbleError("Division by zero", 1, 1)
            out = rval and (lval // rval if lval % rval == 0 else int(lval / rval))
        elif n.op == "%":
            if rval == 0:
                raise PebbleError("Remainder by zero", 1, 1)
            out = lval % rval
        else:  # pragma: no cover
            raise PebbleError(f"Unknown operator {n.op!r}", 1, 1)
        steps.append(f"{lval} {n.op} {rval} = {out}")
        return out

    value = rec(node)
    return value, steps
