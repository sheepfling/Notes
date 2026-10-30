# Jorth

> Type: project note  
> Status: current  
> Updated: 2026-08-01

Jorth is a tiny, dependency-free Forth-like interpreter implemented in both
JavaScript and Python. Both implementations intentionally share the same
language and error behavior.

## Run

From this project directory:

```console
node jorth.js example.jorth
python jorth.py example.jorth
```

Both commands print:

```text
120
```

## Validate both implementations

```console
python validate.py
```

The validator runs the same success and failure cases through both CLIs and
checks their output and exit status.

From the repository root, run the project-owned Python tests with:

```shell
python -m pytest projects/jorth/tests
```

The tests use temporary directories for any generated programs. The standalone
validator also requires Node.js; the Python tests exercise its orchestration
without requiring Node.js or running unrelated project scripts.

## Language

Values are finite floating-point numbers. Tokens are separated by arbitrary
whitespace. A `#` starts a line comment.

| Form               | Effect                                             |
|--------------------|----------------------------------------------------|
| `number`           | Push a number.                                     |
| `+ - * /`          | Pop `right`, then `left`; push `left op right`.    |
| `floor`            | Replace the top value with its floor.              |
| `dup`              | Duplicate the top value.                           |
| `swap`             | Exchange the top two values.                       |
| `drop`             | Discard the top value.                             |
| `= != > >= < <=`   | Compare `left` and `right`; push `1` or `0`.       |
| `store name`       | Pop and store a value under `name`.                |
| `name`             | Push a stored variable or call a defined function. |
| `if ... end`       | Pop a condition; run the block when it is nonzero. |
| `def name ... end` | Define a top-level function.                       |
| `ret`              | Return early from a function.                      |
| `print`            | Pop and print one value.                           |
| `dump`             | Print the data stack without changing it.          |

Function calls use a separate return stack, so return addresses never mix with
program data. Definitions are compiled before execution, allowing forward
function references. Recursive functions are supported.

## Deliberate safety behavior

- Stack underflow, unknown words, invalid block structure, and division by zero
  are errors rather than silently producing `NaN` or `undefined`.
- Numeric tokens must be complete decimal literals; text such as `12abc` is not
  parsed as `12`.
- Function and variable names use `[A-Za-z_][A-Za-z0-9_-]*` and cannot shadow
  built-in words.
- A configurable instruction limit prevents runaway recursion.
