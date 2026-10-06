"""trace.py — print tokens, tree, and every step of the math for an expression."""

from __future__ import annotations

from .evaluator import evaluate_with_steps
from .parser import Parser, tree_string
from .tokens import tokenize_line


def trace_expression(text: str, env: dict | None = None) -> str:
    tokens = tokenize_line(text, 1)
    tok_str = " ".join(
        f"{t.kind}:{t.value}@L{t.line}C{t.col}" for t in tokens if t.kind != "EOF"
    )
    node = Parser(tokens).parse_expression()
    tree = tree_string(node)
    value, steps = evaluate_with_steps(node, env or {})
    lines = [f"input:  {text}", f"tokens: {tok_str}", f"tree:   {tree}", "steps:"]
    lines += [f"  {s}" for s in steps] or ["  (single value, no operations)"]
    lines.append(f"value:  {value}")
    return "\n".join(lines)


def main() -> None:  # pragma: no cover
    import sys

    expr = " ".join(sys.argv[1:]) or "2 + 3 * 4"
    print(trace_expression(expr))


if __name__ == "__main__":  # pragma: no cover
    main()
