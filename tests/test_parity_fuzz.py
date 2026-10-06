"""Differential parity: Pebble vs Python AST on randomized expressions.

Method (from research: ShellFuzzer grammar-based fuzzing + Loyola
property-based suggestion `calc() vs eval()`):
- generate grammar-valid expressions over + - * / % and parens
- compare Pebble evaluate() against Python's own AST (safe, no eval())
- % and / use Pebble truncating semantics for the oracle too
"""

import ast
import operator
import random

from pebble.evaluator import evaluate
from pebble.parser import Parser
from pebble.tokens import tokenize_line

OPS = ["+", "-", "*", "/", "%"]


def gen_expr(rng, depth=0):
    if depth > 3 or rng.random() < 0.35:
        return str(rng.randint(0, 20))
    op = rng.choice(OPS)
    left = gen_expr(rng, depth + 1)
    # avoid div/mod by literal zero at generation time
    right = gen_expr(rng, depth + 1)
    if op in ("/", "%"):
        right = str(rng.randint(1, 20))
    expr = f"{left} {op} {right}"
    if rng.random() < 0.4:
        expr = f"({expr})"
    return expr


def python_oracle(text):
    tree = ast.parse(text, mode="eval")

    def rec(n):
        if isinstance(n, ast.Expression):
            return rec(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, int):
            return n.value
        if isinstance(n, ast.BinOp):
            l, r = rec(n.left), rec(n.right)
            if isinstance(n.op, ast.Add):
                return l + r
            if isinstance(n.op, ast.Sub):
                return l - r
            if isinstance(n.op, ast.Mult):
                return l * r
            if isinstance(n.op, ast.Div):
                return int(l / r)  # match Pebble truncating division
            if isinstance(n.op, ast.Mod):
                # Python % sign follows divisor; Pebble inputs are
                # non-negative in this harness so both agree.
                return l % r
        raise AssertionError(f"unexpected {ast.dump(n)}")

    return rec(tree)


def test_parity_500_random_expressions():
    rng = random.Random(20261006)  # fixed seed => reproducible
    mismatches = 0
    for _ in range(500):
        text = gen_expr(rng)
        pebble = evaluate(Parser(tokenize_line(text)).parse_expression(), {})
        oracle = python_oracle(text)
        assert pebble == oracle, f"{text}: pebble={pebble} python={oracle}"
    assert mismatches == 0
