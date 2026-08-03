# Validation report

> Type: validation record  
> Status: current  
> Updated: 2026-08-01

## Original defects corrected

1. Tokenization split only on a literal space or newline, leaving empty tokens,
   tabs, and carriage returns problematic.
2. `parseFloat` accepted partial numeric tokens such as `12abc`.
3. Function calls changed the program counter and then incremented it again,
   skipping the first token in every function body.
4. Function definitions similarly skipped the token immediately following the
   closing `end`.
5. The same `end` operation represented both conditional closure and function
   return, so a true `if` block could pop ordinary data as a return address.
6. Return addresses shared the data stack.
7. `<` accidentally implemented `<=`; ordered comparisons also used reversed
   operands.
8. Unknown words and stack underflow were silently ignored or converted to
   JavaScript `undefined`/`NaN` behavior.

## Corrected semantics

- A compile pass matches every `if ... end` and `def ... end` block before
  execution.
- Functions use a separate return stack.
- Binary words consistently interpret `left right op` as `left op right`.
- `if` consumes its condition, matching ordinary Forth stack behavior.
- Both implementations reject malformed programs with source locations.
- JavaScript and Python use the same tokenizer, names, words, numeric grammar,
  output format, and instruction limit.

## Executed checks

```console
python validate.py
PASS: 10 success cases and 9 error cases across both implementations (38 interpreter runs).

python -m py_compile jorth.py validate.py
node --check jorth.js

python jorth.py example.jorth
120

node jorth.js example.jorth
120
```

The shared cases cover arithmetic and operand order, stack words, variables,
functions, nested conditionals, recursion and early return, comments and mixed
whitespace, forward function references, stack dumps, and nine structured error
conditions.
