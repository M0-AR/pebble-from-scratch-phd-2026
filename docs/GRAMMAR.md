# Pebble grammar (implemented, tested, frozen for v1.0.0)

```ebnf
program    = { statement } ;
statement  = "let" NAME "=" expression
           | "print" expression ;
expression = term { ("+" | "-") term } ;      (* left-assoc, loosest *)
term       = factor { ("*" | "/" | "%") factor } ; (* left-assoc, tighter *)
factor     = NUMBER | NAME | "(" expression ")" ;
NUMBER     = digit { digit } ;
NAME       = letter { letter | digit | "_" } ;
```

## Consequences (all covered by tests)

- `2 + 3 * 4` parses as `(+ 2 (* 3 4))` = 14. Precedence is structural:
  `expression` calls `term` calls `factor`; tighter ops sit deeper.
- `2 - 3 - 4` parses as `(- (- 2 3) 4)` = -5 (left loop, not recursion).
- `(2 + 3) * 4` parses as `(* (+ 2 3) 4)` = 20: `factor -> '(' expression ')'`
  re-enters at the top, so brackets override.
- `17 % 5` parses as `(% 17 5)` = 2: `%` lives in `term`, same level as `*`/`/`.
- Trailing tokens are errors: `2 + 3 4` -> `Unexpected '4' after expression`.
- `2 * * 3` -> `Expected a number, name, or '(' but found '*'` at the second `*`.
- `print (1 + 2` -> `Expected ')' ...` at end-of-line (transcript quick-check).
- Integers only; `/` is truncating (`7 / 2 = 3`); `/ 0` and `% 0` are
  `PebbleError`, never a Python traceback.

## Deliberate deviations from the transcript (documented, tested)

- Names allow a leading/trailing `_` (`_x`, `count_2`): superset of
  "letters or digits", matches Python identifier practice; pure-letter
  programs behave identically.
- `take()` reports `the end of the line` for EOF instead of `''`, so the
  transcript's "Expected a closing bracket, but found the end of the line"
  appears verbatim.

## Extensions (not in v1 core, roadmap)

- Unary minus: add `unary = ("-" unary) | power`-style level between
  `term` and `factor` (cf. Loyola guide `unary -> power`).
- Power `^`/`**`: right-assoc via `if` + recursion (not loop).
  `2 ^ 3 ^ 2 = 2 ^ (3 ^ 2) = 512`.
