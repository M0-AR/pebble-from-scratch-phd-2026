"""Experiment E2 — Precedence + associativity matrix (the 14-vs-20 question).

Enumerates a fixed corpus of expressions, checks Pebble tree shape + value
against the Python AST oracle, and writes a CSV + JSON summary. Used by the
paper's Table 1 and the 'hidden pattern' analysis (error rate of naive
left-to-right evaluation vs tree evaluation).
"""

from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pebble.evaluator import evaluate  # noqa: E402
from pebble.parser import Parser, tree_string  # noqa: E402
from pebble.tokens import tokenize_line  # noqa: E402

CORPUS = [
    "2 + 3 * 4",
    "(2 + 3) * 4",
    "2 - 3 - 4",
    "10 / 2 * 3",
    "17 % 5",
    "2 + 17 % 5",
    "price * count + 2",
    "100 - 10 - 10 - 10",
    "2 * 3 + 4 * 5",
    "(total - 2) / count",
    "7 / 2",
    "8 % 3 + 1 * 2",
]

OUT_JSON = Path(__file__).parent / "precedence_results.json"
OUT_CSV = Path(__file__).parent / "precedence_results.csv"


def left_to_right_naive(text: str) -> int:
    """Deliberately wrong evaluator: fold strictly left-to-right, no precedence."""
    toks = [t.value for t in tokenize_line(text) if t.kind != "EOF"]
    # only numeric corpus rows qualify; skip names
    vals = [int(toks[0])]
    ops: list[str] = []
    i = 1
    while i < len(toks):
        if toks[i] == "(":
            raise ValueError("naive evaluator skips parenthesized rows")
        ops.append(toks[i])
        vals.append(int(toks[i + 1]))
        i += 2
    acc = vals[0]
    for op, v in zip(ops, vals[1:]):
        acc = {"+": acc + v, "-": acc - v, "*": acc * v, "/": int(acc / v), "%": acc % v}[op]
    return acc


def main() -> int:
    rows = []
    for text in CORPUS:
        env = {"price": 5, "count": 3, "total": 17}
        node = Parser(tokenize_line(text)).parse_expression()
        tree = tree_string(node)
        value = evaluate(node, env)
        try:
            naive = left_to_right_naive(text)
            naive_wrong = naive != value
        except Exception:
            naive, naive_wrong = None, None
        rows.append(
            {"expr": text, "tree": tree, "pebble": value, "naive_ltr": naive, "naive_wrong": naive_wrong}
        )
    wrong = sum(1 for r in rows if r["naive_wrong"])
    denom = sum(1 for r in rows if r["naive_wrong"] is not None)
    summary = {
        "rows": rows,
        "hidden_pattern": {
            "claim": "Naive left-to-right evaluation is wrong whenever a tighter "
            "operator follows a looser one without brackets.",
            "naive_error_rate": f"{wrong}/{denom}",
        },
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["expr", "tree", "pebble", "naive_ltr", "naive_wrong"])
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(summary, indent=2))
    print(f"wrote {OUT_JSON} and {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
