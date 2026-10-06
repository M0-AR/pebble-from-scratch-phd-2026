"""Stage 1 — Tokenizer: characters -> tokens.

Rule (from transcript + verified against CPython lexical-analysis docs):
- digit starts NUMBER, continues while digits
- letter/underscore starts NAME, continues while letters/digits/underscore
- '+','-','*','/','%','=','(',')' are single-char tokens
- spaces/tabs skipped; line/col tracked per token
- 'let' and 'print' are KEYWORDs, everything else is NAME
- any other character is a lexical error with line/col
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .errors import PebbleError

KEYWORDS = {"let", "print"}
SINGLE_SYMBOLS = set("+-*/%=()")


@dataclass
class Token:
    kind: str  # 'NUMBER' | 'NAME' | 'KEYWORD' | 'OP' | 'EOF'
    value: str
    line: int
    col: int  # 1-based column where the token started

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Token({self.kind},{self.value!r},L{self.line}C{self.col})"


def tokenize_line(text: str, line: int = 1) -> List[Token]:
    """Tokenize one line. Appends an EOF marker (needed by the parser)."""
    tokens: List[Token] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        col = i + 1  # 1-based
        if ch in (" ", "\t", "\r"):
            i += 1
            continue
        if ch.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            tokens.append(Token("NUMBER", text[i:j], line, col))
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            word = text[i:j]
            kind = "KEYWORD" if word in KEYWORDS else "NAME"
            tokens.append(Token(kind, word, line, col))
            i = j
            continue
        if ch in SINGLE_SYMBOLS:
            tokens.append(Token("OP", ch, line, col))
            i += 1
            continue
        raise PebbleError(f"Unexpected character {ch!r}", line, col)
    tokens.append(Token("EOF", "", line, n + 1))
    return tokens


def tokenize_program(source: str) -> List[List[Token]]:
    """Tokenize a whole program line-by-line (keeps per-line columns exact)."""
    lines = source.splitlines() or [""]
    return [tokenize_line(text, idx + 1) for idx, text in enumerate(lines)]
