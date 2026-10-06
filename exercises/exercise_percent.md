"""Exercise 1 (the video's task): add `%` — the remainder operator.

Goal: `print 17 % 5` prints `2`.

You touch all three stages (this is the whole point — one level per stage):

1. TOKENIZER (`pebble/tokens.py`): the character must become a token.
   - Add `'%'` to the single-symbol set. Done already in this repo —
     find `SINGLE_SYMBOLS` and confirm.
   - Check: `tokenize_line("17 % 5")` -> [17, %, 5].

2. PARSER (`pebble/parser.py`, method `term`):
   - `%` binds exactly like `*` and `/` (tighter than `+`).
   - So the `while` condition in `term()` must include `"%"`.
   - Check: tree of `2 + 17 % 5` is `(+ 2 (% 17 5))`, NOT `(% (+ 2 17) 5)`.

3. EVALUATOR (`pebble/evaluator.py`, function `evaluate` + `evaluate_with_steps`):
   - Add `if node.op == "%": return left % right`
   - Plus a `Remainder by zero` error mirroring division.
   - Check: `17 % 5 == 2`; `10 % 3 == 1`.

Verify (do not skip):
```
python3 -m pebble --trace '17 % 5'
pytest tests/test_parser.py::test_percent_binds_like_times tests/test_interpreter.py::test_percent_value -q
python3 experiments/precedence_experiment.py
```

Extension (in repo, with tests): negative numbers and powers.
- The transcript mentions them as follow-ups; see `docs/GRAMMAR.md#extensions`.
"""
