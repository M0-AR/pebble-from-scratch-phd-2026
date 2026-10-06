"""Evaluator + interpreter tests: transcript values locked in."""

from pebble.errors import PebbleError
from pebble.evaluator import evaluate
from pebble.interpreter import run_program
from pebble.parser import Parser
from pebble.tokens import tokenize_line


def ev(text, env=None):
    return evaluate(Parser(tokenize_line(text)).parse_expression(), env or {})


def test_fourteen_not_twenty():
    assert ev("2 + 3 * 4") == 14
    assert ev("(2 + 3) * 4") == 20


def test_left_assoc_value():
    assert ev("2 - 3 - 4") == -5


def test_percent_value():
    assert ev("17 % 5") == 2


def test_division():
    assert ev("15 / 3") == 5
    assert ev("7 / 2") == 3  # truncating integer division, documented


def test_division_by_zero_is_pebble_error_not_crash():
    try:
        ev("1 / 0")
        raise AssertionError("should raise")
    except PebbleError as e:
        assert "zero" in str(e).lower()


def test_transcript_program_prints_17_then_5():
    src = "let price = 5\nlet count = 3\nlet total = price * count + 2\nprint total\nprint (total - 2) / count\n"
    outputs, env = run_program(src)
    assert outputs == [17, 5]
    assert env == {"price": 5, "count": 3, "total": 17}


def test_undefined_name_reports_line():
    try:
        run_program("let x = 5\nprint prise\n")
        raise AssertionError("should raise")
    except PebbleError as e:
        assert e.line == 2
        assert "prise" in str(e)


def test_let_requires_equals_and_name():
    for bad in ["let = 5", "let 5 = 3", "print", "2 + 3"]:
        try:
            run_program(bad + "\n")
            raise AssertionError(f"should raise for {bad!r}")
        except PebbleError:
            pass
