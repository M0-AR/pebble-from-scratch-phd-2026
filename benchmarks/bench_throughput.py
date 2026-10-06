"""Benchmark B1 — Throughput: tokenize / parse / evaluate tokens-per-second.

Method: time each stage separately over N=20000 iterations of the transcript's
canonical line `let total = price * count + 2`, plus end-to-end programs/sec.
Writes JSON for the paper's Figure 2. Stdlib only (timeit + statistics).
"""

from __future__ import annotations

import json
import statistics
import sys
import timeit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pebble.evaluator import evaluate  # noqa: E402
from pebble.interpreter import run_program  # noqa: E402
from pebble.parser import Parser  # noqa: E402
from pebble.tokens import tokenize_line  # noqa: E402

LINE = "let total = price * count + 2"
EXPR = "price * count + 2"
ENV = {"price": 5, "count": 3}
PROGRAM = "let price = 5\nlet count = 3\nlet total = price * count + 2\nprint total\nprint (total - 2) / count\n"


def bench(fn, number=20000, repeat=7):
    times = timeit.repeat(fn, number=number, repeat=repeat)
    per_op_us = [t / number * 1e6 for t in times]
    return {"median_us": statistics.median(per_op_us), "min_us": min(per_op_us), "runs": per_op_us}


def main() -> int:
    toks = tokenize_line(EXPR)
    tok_res = bench(lambda: tokenize_line(EXPR))
    node = Parser(tokenize_line(EXPR)).parse_expression()
    parse_res = bench(lambda: Parser(tokenize_line(EXPR)).parse_expression())
    eval_res = bench(lambda: evaluate(node, ENV))
    prog_res = bench(lambda: run_program(PROGRAM), number=2000)
    n_tokens = len([t for t in toks if t.kind != "EOF"])
    result = {
        "line": LINE,
        "tokens_per_expr": n_tokens,
        "tokenize_us_per_line": tok_res,
        "parse_us_per_expr": parse_res,
        "evaluate_us_per_expr": eval_res,
        "program_us_end_to_end": prog_res,
        "derived": {
            "tokens_per_sec": 1e6 / tok_res["median_us"] * n_tokens,
            "exprs_parsed_per_sec": 1e6 / parse_res["median_us"],
            "exprs_evaluated_per_sec": 1e6 / eval_res["median_us"],
        },
    }
    out = Path(__file__).parent / "throughput_results.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
