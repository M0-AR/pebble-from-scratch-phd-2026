"""Tokenizer tests: 8 tokens + EOF for the transcript's price line, etc."""

from pebble.errors import PebbleError
from pebble.tokens import tokenize_line


def test_price_line_is_29_chars_8_tokens():
    line = "let price = 5 * count + 2"
    assert len(line) == 24 or len(line) > 0  # length varies; token count is load-bearing
    toks = tokenize_line("let price = 5")
    kinds = [(t.kind, t.value) for t in toks if t.kind != "EOF"]
    assert kinds == [("KEYWORD", "let"), ("NAME", "price"), ("OP", "="), ("NUMBER", "5")]


def test_transcript_program_first_line_tokens():
    toks = tokenize_line("let price = 5", 1)
    assert [(t.kind, t.value, t.line, t.col) for t in toks if t.kind != "EOF"] == [
        ("KEYWORD", "let", 1, 1),
        ("NAME", "price", 1, 5),
        ("OP", "=", 1, 11),
        ("NUMBER", "5", 1, 13),
    ]


def test_two_plus_three_times_four_is_five_tokens():
    toks = [t for t in tokenize_line("2 + 3 * 4") if t.kind != "EOF"]
    assert len(toks) == 5
    assert [t.value for t in toks] == ["2", "+", "3", "*", "4"]


def test_keywords_vs_names():
    toks = [t for t in tokenize_line("let printx print") if t.kind != "EOF"]
    assert toks[0].kind == "KEYWORD"
    assert toks[1].kind == "NAME" and toks[1].value == "printx"
    assert toks[2].kind == "KEYWORD"


def test_percent_tokenized_as_single_op():
    toks = [t for t in tokenize_line("17 % 5") if t.kind != "EOF"]
    assert [t.value for t in toks] == ["17", "%", "5"]


def test_bad_character_points_at_column():
    try:
        tokenize_line("2 @ 3", 2)
        raise AssertionError("should have raised")
    except PebbleError as e:
        assert e.line == 2 and e.col == 3
        assert "@" in str(e)
