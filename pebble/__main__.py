"""CLI: python -m pebble program.pebble | python -m pebble --trace '2 + 3 * 4'."""

from __future__ import annotations

import sys

from .errors import PebbleError
from .interpreter import run_program
from .trace import trace_expression


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args and args[0] == "--trace":
        try:
            print(trace_expression(" ".join(args[1:]) or "2 + 3 * 4"))
        except PebbleError as e:
            print(e.render(), file=sys.stderr)
            return 1
        return 0
    if args:
        try:
            with open(args[0], encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            print(f"cannot read {args[0]}: {e}", file=sys.stderr)
            return 1
    else:
        source = sys.stdin.read()
    lines = source.splitlines() or [""]
    try:
        outputs, _ = run_program(source)
    except PebbleError as e:
        raw = ""
        try:
            raw = lines[e.line - 1] if 1 <= e.line <= len(lines) else ""
        except IndexError:
            raw = ""
        print(e.render(raw), file=sys.stderr)
        return 1
    for v in outputs:
        print(v)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
