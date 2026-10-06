"""Parser tests: precedence falls out of the call chain, not a table."""

from pebble.parser import Parser, tree_string
from pebble.tokens import tokenize_line


def parse(text):
    return Parser(tokenize_line(text)).parse_expression()


def test_plus_at_top_times_below_right():
    assert tree_string(parse("2 + 3 * 4")) == "(+ 2 (* 3 4))"


def test_brackets_flip_the_tree():
    assert tree_string(parse("(2 + 3) * 4")) == "(* (+ 2 3) 4)"


def test_left_assoc_minus():
    # 2-3-4 must be ((2-3)-4) = -5, not (2-(3-4)) = 3
    assert tree_string(parse("2 - 3 - 4")) == "(- (- 2 3) 4)"


def test_left_assoc_term_level():
    assert tree_string(parse("10 / 2 * 3")) == "(* (/ 10 2) 3)"
    assert tree_string(parse("17 % 5 % 2")) == "(% (% 17 5) 2)"


def test_percent_binds_like_times():
    # % lives in term(): tighter than +.
    assert tree_string(parse("2 + 17 % 5")) == "(+ 2 (% 17 5))"
    assert tree_string(parse("price * count + 2")) == "(+ (* price count) 2)"


def test_missing_close_bracket_names_what_was_wanted():
    from pebble.errors import PebbleError

    try:
        parse("print (1 + 2".replace("print ", ""))
        raise AssertionError("should raise")
    except PebbleError as e:
        assert "')'" in str(e) or "closing bracket" in str(e).lower() or ")" in str(e)


def test_trailing_garbage_rejected():
    from pebble.errors import PebbleError

    try:
        parse("2 + 3 4")
        raise AssertionError("should raise")
    except PebbleError as e:
        assert "Unexpected" in str(e)


def test_double_star_error_points_at_second_star():
    from pebble.errors import PebbleError

    try:
        parse("2 * * 3")
        raise AssertionError("should raise")
    except PebbleError as e:
        # second '*' is at column 5 in "2 * * 3"
        assert e.col == 5, f"caret col {e.col} != 5"
        assert "number" in str(e).lower()
