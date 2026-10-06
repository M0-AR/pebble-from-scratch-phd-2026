# Benchmark & reproducibility method

All numbers in `README.md` come from scripts in this repo — no hand-typed
figures. Re-run everything with one command:

```bash
docker compose up --build          # runs tests + E1 + E2 + B1, drops JSON/CSV
# or without docker:
pip install -r requirements.txt
pytest tests/ -q
python experiments/precedence_experiment.py
python experiments/live_market_validation.py --snapshot-only
python benchmarks/bench_throughput.py
```

## What each artifact proves

| Artifact | Method | Oracle | Reproducibility |
|---|---|---|---|
| `tests/test_parity_fuzz.py` | 500 grammar-generated exprs, seed `20261006` | Python `ast` (never `eval`) | deterministic, 23 tests pass |
| `experiments/precedence_experiment.py` | fixed 12-expr corpus, tree + value | Python AST + naive-LTR control | CSV+JSON committed |
| `experiments/live_market_validation.py` | live BTC+Fiat via CoinGecko/Frankfurter, snapshot fallback | same integer math in Python | `--snapshot-only` is hermetic |
| `benchmarks/bench_throughput.py` | `timeit.repeat`, 20k iters x7, median | n/a (throughput) | JSON with all 7 runs |

## Hidden-pattern analysis (E2)

The naive left-to-right evaluator (no precedence) is included as a control.
On the 9 unparenthesized numeric rows it is wrong 3/9 times (33%) — exactly
on rows where a tighter operator follows a looser one (`2 + 3 * 4`,
`8 % 3 + 1 * 2`, ...). That is the paper's "hidden pattern": precedence
errors are not random; they cluster on loose-tight adjacencies, which is why
a tree (not a longer left-to-right pass) is the fix.

## Environment

- Python 3.10+ (uses `X | Y` unions), stdlib only, no third-party imports
  in `pebble/`.
- Docker image `python:3.12-slim`, same commands as above.
- Live-market numbers are pinned in `experiments/live_market_results.json`
  with `mode: live|snapshot` so readers can tell which path ran.
