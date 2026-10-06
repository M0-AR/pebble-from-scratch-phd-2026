"""Experiment E1 — Live-market validation: Pebble arithmetic on real 2026 data.

What it does (zero-to-hero verification, no API keys):
1. Fetch live BTC price (CoinGecko keyless) + USD->EUR/GBP/JPY (Frankfurter/ECB).
2. Build Pebble programs from the live numbers, e.g.
     let price = 86158
     let count = 3
     let total = price * count + 2
     print total
3. Evaluate the SAME formula in Pebble and in Pythonką AST oracle.
4. Assert bitwise equality and write results JSON.

If the network is blocked, falls back to the pinned snapshot taken during
research (BTC 86158 USD @ 2026-10-06; EUR 0.89254, GBP 0.75616, JPY 158.23)
so the experiment is always reproducible. Both paths are reported.

Run: python experiments/live_market_validation.py [--snapshot-only]
"""

from __future__ import annotations

import ast
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pebble.interpreter import run_program  # noqa: E402

SNAPSHOT = {
    "btc_usd": 86158,
    "eur": 0.89254,
    "gbp": 0.75616,
    "jpy": 158.23,
    "asof": "2026-10-05",
}

OUT = Path(__file__).parent / "live_market_results.json"


def fetch_live(timeout: int = 12) -> dict:
    """Best-effort live fetch; raises on any failure so caller can fallback."""
    btc = None
    try:
        with urllib.request.urlopen(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            timeout=timeout,
        ) as r:
            btc = json.load(r)["bitcoin"]["usd"]
    except Exception:
        pass
    fx = {}
    try:
        with urllib.request.urlopen(
            "https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY", timeout=timeout
        ) as r:
            fx = json.load(r).get("rates", {})
    except Exception:
        pass
    if btc is None or not fx:
        raise RuntimeError("live fetch incomplete")
    return {
        "btc_usd": int(btc),
        "eur": float(fx["EUR"]),
        "gbp": float(fx["GBP"]),
        "jpy": float(fx["JPY"]),
        "asof": datetime.now(timezone.utc).date().isoformat(),
    }


def pebble_eval(program: str) -> list[int]:
    outputs, _ = run_program(program)
    return outputs


def main() -> int:
    snapshot_only = "--snapshot-only" in sys.argv
    live, mode = None, "snapshot"
    if not snapshot_only:
        try:
            live = fetch_live()
            mode = "live"
        except Exception as e:
            print(f"[warn] live fetch failed ({e}); using snapshot", file=sys.stderr)
    data = live or SNAPSHOT
    btc = int(data["btc_usd"])
    # Integer milli-units so Pebble (int-only) can handle FX exactly.
    eur_m = int(round(float(data["eur"]) * 1000))
    count = 3
    fee = 2
    program = (
        f"let price = {btc}\nlet count = {count}\n"
        f"let total = price * count + {fee}\nprint total\n"
        f"print (total - {fee}) / count\nprint total % count\n"
        f"let eurm = {eur_m}\nprint eurm * count\n"
    )
    outputs, env = run_program(program)
    # Oracle: same math in plain Python integers.
    total = btc * count + fee
    expected = [total, (total - fee) // count, total % count, eur_m * count]
    passed = outputs == expected
    result = {
        "mode": mode,
        "asof": data.get("asof"),
        "inputs": {"btc_usd": btc, "count": count, "fee": fee, "eur_milli": eur_m},
        "pebble_program": program,
        "pebble_outputs": outputs,
        "python_expected": expected,
        "passed": passed,
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"wrote {OUT}")
    # Also show Python bytecode contrast for 2+3*4 (constant folding demo).
    import dis
    import io

    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        dis.dis(compile("2 + 3 * 4", "<demo>", "eval"))
    finally:
        sys.stdout = old
    print("--- CPython bytecode for 2 + 3 * 4 (note: folded to 14) ---")
    print(buf.getvalue())
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
