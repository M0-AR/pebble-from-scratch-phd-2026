"""Pebble in one file (~200 lines, stdlib only). Checkpoint of the full pipeline.
Usage: python checkpoints/pebble_single.py program.pebble
       python checkpoints/pebble_single.py --trace '2 + 3 * 4'
"""
from __future__ import annotations
import sys
from dataclasses import dataclass
from typing import List


@dataclass
class PebbleError(Exception):
    message: str; line: int = 1; col: int = 1
    def __str__(self): return f"[line {self.line}, col {self.col}] {self.message}"
    def render(self, src=""):
        if not src: return str(self)
        return f"{self}\n{src}\n{' ' * (max(1, self.col) - 1)}^"


@dataclass
class Token:
    kind: str; value: str; line: int; col: int


KEYWORDS = {"let", "print"}
SYMBOLS = set("+-*/%=()")


def tokenize_line(text: str, line: int = 1) -> List[Token]:
    toks: List[Token] = []; i = 0; n = len(text)
    while i < n:
        ch = text[i]; col = i + 1
        if ch in " \t\r": i += 1; continue
        if ch.isdigit():
            j = i
            while j < n and text[j].isdigit(): j += 1
            toks.append(Token("NUMBER", text[i:j], line, col)); i = j; continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"): j += 1
            w = text[i:j]
            toks.append(Token("KEYWORD" if w in KEYWORDS else "NAME", w, line, col)); i = j; continue
        if ch in SYMBOLS:
            toks.append(Token("OP", ch, line, col)); i += 1; continue
        raise PebbleError(f"Unexpected character {ch!r}", line, col)
    toks.append(Token("EOF", "", line, n + 1))
    return toks


@dataclass
class Number:
    value: int; line: int = 1; col: int = 1


@dataclass
class Var:
    name: str; line: int = 1; col: int = 1


@dataclass
class BinOp:
    op: str; left: object; right: object


class Parser:
    def __init__(self, toks: List[Token]): self.toks = toks; self.pos = 0
    def peek(self): return self.toks[self.pos]
    def advance(self):
        t = self.toks[self.pos]
        if self.pos < len(self.toks) - 1: self.pos += 1
        return t
    def take(self, kind, value=""):
        t = self.peek()
        if t.kind != kind or (value and t.value != value):
            want = repr(value) if value else kind.lower()
            found = "the end of the line" if t.kind == "EOF" else repr(t.value)
            raise PebbleError(f"Expected {want}, but found {found}", t.line, t.col)
        return self.advance()
    def expression(self):
        node = self.term()
        while self.peek().kind == "OP" and self.peek().value in ("+", "-"):
            op = self.advance().value
            node = BinOp(op, node, self.term())
        return node
    def term(self):
        node = self.factor()
        while self.peek().kind == "OP" and self.peek().value in ("*", "/", "%"):
            op = self.advance().value
            node = BinOp(op, node, self.factor())
        return node
    def factor(self):
        t = self.peek()
        if t.kind == "NUMBER": self.advance(); return Number(int(t.value), t.line, t.col)
        if t.kind == "NAME": self.advance(); return Var(t.value, t.line, t.col)
        if t.kind == "OP" and t.value == "(":
            self.advance(); node = self.expression(); self.take("OP", ")"); return node
        if t.kind == "EOF":
            raise PebbleError("Expected a number, name, or '(' but found the end of the line", t.line, t.col)
        raise PebbleError(f"Expected a number, name, or '(' but found {t.value!r}", t.line, t.col)
    def parse_expression(self):
        node = self.expression()
        t = self.peek()
        if t.kind != "EOF": raise PebbleError(f"Unexpected {t.value!r} after expression", t.line, t.col)
        return node


def tree(n):
    if isinstance(n, Number): return str(n.value)
    if isinstance(n, Var): return n.name
    return f"({n.op} {tree(n.left)} {tree(n.right)})"


def ev(n, env: dict):
    if isinstance(n, Number): return n.value
    if isinstance(n, Var):
        if n.name not in env: raise PebbleError(f"Undefined name {n.name!r}", n.line, n.col)
        return env[n.name]
    l = ev(n.left, env); r = ev(n.right, env)
    if n.op == "+": return l + r
    if n.op == "-": return l - r
    if n.op == "*": return l * r
    if n.op == "/":
        if r == 0: raise PebbleError("Division by zero", 1, 1)
        return l // r if l % r == 0 else int(l / r)
    if n.op == "%":
        if r == 0: raise PebbleError("Remainder by zero", 1, 1)
        return l % r
    raise PebbleError(f"Unknown operator {n.op!r}", 1, 1)


def parse_stmt(toks: List[Token]):
    p = Parser(toks); f = p.peek()
    if f.kind == "KEYWORD" and f.value == "let":
        p.advance(); name = p.take("NAME"); p.take("OP", "="); e = p.expression()
        t = p.peek()
        if t.kind != "EOF": raise PebbleError(f"Unexpected {t.value!r} after expression", t.line, t.col)
        return ("let", name.value, e, f.line)
    if f.kind == "KEYWORD" and f.value == "print":
        p.advance(); e = p.expression()
        t = p.peek()
        if t.kind != "EOF": raise PebbleError(f"Unexpected {t.value!r} after expression", t.line, t.col)
        return ("print", e, f.line)
    if f.kind == "EOF": raise PebbleError("Empty statement", f.line, f.col)
    raise PebbleError(f"Expected 'let' or 'print' but found {f.value!r}", f.line, f.col)


def run(source: str):
    out: List[int] = []; env: dict = {}
    lines = source.splitlines() or [""]
    for idx, raw in enumerate(lines, 1):
        if not raw.strip(): continue
        stmt = parse_stmt(tokenize_line(raw, idx))
        if stmt[0] == "let":
            _, name, e, _ = stmt; env[name] = ev(e, env)
        else:
            _, e, ln = stmt
            try: out.append(ev(e, env))
            except PebbleError as ex: raise PebbleError(ex.message, ln, ex.col) from None
    return out, env


def trace(text: str):
    toks = tokenize_line(text)
    node = Parser(toks).parse_expression()
    print("tokens:", " ".join(f"{t.value}@C{t.col}" for t in toks if t.kind != "EOF"))
    print("tree:  ", tree(node))
    print("value: ", ev(node, {}))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--trace": trace(" ".join(a[1:]) or "2 + 3 * 4")
    else:
        src = open(a[0]).read() if a else sys.stdin.read()
        try:
            for v in run(src)[0]: print(v)
        except PebbleError as e:
            ls = (src.splitlines() or [""])
            raw = ls[e.line - 1] if 1 <= e.line <= len(ls) else ""
            print(e.render(raw), file=sys.stderr); sys.exit(1)
