"""Pebble errors: every error carries line + column and renders a caret.

Best-practice synthesis from the research sweep:
- Loyola recursive-descent guide + Crafting Interpreters: errors must name
  what was wanted, what was found, and where (line/col).
- CPython tokenizer docs: lexical errors point at the offending character.
- Transcript rule: factor knows what it wanted (number/name/bracket).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PebbleError(Exception):
    message: str
    line: int = 1
    col: int = 1

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[line {self.line}, col {self.col}] {self.message}"

    def render(self, source_line: str = "") -> str:
        """Render two-line diagnostic with a caret under the column."""
        header = f"[line {self.line}, col {self.col}] {self.message}"
        if not source_line:
            return header
        # col is 1-based; clamp caret inside the line.
        caret_pos = max(1, self.col)
        caret = " " * (caret_pos - 1) + "^"
        return f"{header}\n{source_line}\n{caret}"
