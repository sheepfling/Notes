#!/usr/bin/env python3
"""A small, deterministic Forth-like stack-language interpreter."""

from __future__ import annotations

import math
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

NUMBER_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
WORD_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
RESERVED_WORDS: frozenset[str] = frozenset(
    {
        "+",
        "-",
        "*",
        "/",
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "floor",
        "dup",
        "swap",
        "drop",
        "if",
        "def",
        "end",
        "ret",
        "store",
        "print",
        "dump",
    }
)

type Output = Callable[[str], None]
type BlockKind = Literal["if", "def"]


class JorthError(RuntimeError):
    """A source-aware Jorth compile or runtime error."""

    def __init__(self, message: str, token: Token | None = None) -> None:
        location = "" if token is None else f" at {token.line}:{token.column}"
        super().__init__(f"{message}{location}")
    ####


####


@dataclass(frozen=True, slots=True)
class Token:
    text: str
    line: int
    column: int


####


@dataclass(frozen=True, slots=True)
class Function:
    start: int
    end: int


####


@dataclass(frozen=True, slots=True)
class Block:
    kind: BlockKind
    index: int
    token: Token
    name: str | None = None
    body_start: int | None = None


####


@dataclass(frozen=True, slots=True)
class CompiledProgram:
    tokens: tuple[Token, ...]
    if_false_jumps: dict[int, int]
    definition_jumps: dict[int, int]
    conditional_ends: frozenset[int]
    function_ends: frozenset[int]
    functions: dict[str, Function]


####


def tokenize(source: str) -> tuple[Token, ...]:
    """Split source into whitespace-delimited tokens with ``#`` comments."""
    tokens: list[Token] = []

    for line_number, line in enumerate(source.splitlines(), start=1):
        uncommented = line.split("#", maxsplit=1)[0]
        for match in re.finditer(r"\S+", uncommented):
            tokens.append(
                Token(
                    text=match.group(0),
                    line=line_number,
                    column=match.start() + 1,
                )
            )
        ####
    ####

    return tuple(tokens)


####


def is_number_token(text: str) -> bool:
    return NUMBER_PATTERN.fullmatch(text) is not None


####


def format_number(value: float) -> str:
    if value == 0.0:
        return "0"
    ####
    if value.is_integer():
        return str(int(value))
    ####
    return str(value)


####


def validate_word_name(token: Token) -> None:
    if WORD_PATTERN.fullmatch(token.text) is None or token.text in RESERVED_WORDS:
        raise JorthError(f"invalid word name '{token.text}'", token)
    ####


####


def compile_source(source: str) -> CompiledProgram:
    tokens = tokenize(source)
    if_false_jumps: dict[int, int] = {}
    definition_jumps: dict[int, int] = {}
    conditional_ends: set[int] = set()
    function_ends: set[int] = set()
    functions: dict[str, Function] = {}
    declared_functions: set[str] = set()
    store_targets: list[Token] = []
    blocks: list[Block] = []

    index = 0
    while index < len(tokens):
        token = tokens[index]

        if token.text == "def":
            if blocks:
                raise JorthError("'def' is only valid at top level", token)
            ####
            if index + 1 >= len(tokens):
                raise JorthError("'def' requires a function name", token)
            ####

            name_token = tokens[index + 1]
            validate_word_name(name_token)
            if name_token.text in declared_functions:
                raise JorthError(f"duplicate function '{name_token.text}'", name_token)
            ####

            declared_functions.add(name_token.text)
            blocks.append(
                Block(
                    kind="def",
                    index=index,
                    token=token,
                    name=name_token.text,
                    body_start=index + 2,
                )
            )
            index += 2
            continue
        elif token.text == "store":
            if index + 1 >= len(tokens):
                raise JorthError("'store' requires a variable name", token)
            ####

            name_token = tokens[index + 1]
            validate_word_name(name_token)
            store_targets.append(name_token)
            index += 2
            continue
        elif token.text == "if":
            blocks.append(Block(kind="if", index=index, token=token))
        elif token.text == "ret":
            inside_function = any(block.kind == "def" for block in blocks)
            if not inside_function:
                raise JorthError("'ret' is only valid inside a function", token)
            ####
        elif token.text == "end":
            if not blocks:
                raise JorthError("unmatched 'end'", token)
            ####

            block = blocks.pop()
            if block.kind == "if":
                if_false_jumps[block.index] = index + 1
                conditional_ends.add(index)
            else:
                assert block.name is not None
                assert block.body_start is not None
                functions[block.name] = Function(start=block.body_start, end=index)
                definition_jumps[block.index] = index + 1
                function_ends.add(index)
            ####
        ####

        index += 1
    ####

    if blocks:
        block = blocks[-1]
        raise JorthError(f"unclosed '{block.kind}'", block.token)
    ####

    for target in store_targets:
        if target.text in declared_functions:
            raise JorthError(
                f"variable '{target.text}' conflicts with a function",
                target,
            )
        ####
    ####

    return CompiledProgram(
        tokens=tokens,
        if_false_jumps=if_false_jumps,
        definition_jumps=definition_jumps,
        conditional_ends=frozenset(conditional_ends),
        function_ends=frozenset(function_ends),
        functions=functions,
    )


####


class JorthVM:
    """Execute compiled Jorth programs with separate data and return stacks."""

    def __init__(
            self,
            *,
            output: Output = print,
            max_steps: int = 1_000_000,
    ) -> None:
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        ####
        self.output = output
        self.max_steps = max_steps
        self.stack: list[float] = []
        self.return_stack: list[int] = []
        self.variables: dict[str, float] = {}

    ####

    def run(self, source: str) -> list[float]:
        program = compile_source(source)
        self.stack = []
        self.return_stack = []
        self.variables = {}

        pc = 0
        steps = 0

        while pc < len(program.tokens):
            steps += 1
            if steps > self.max_steps:
                raise JorthError(
                    f"step limit exceeded ({self.max_steps})",
                    program.tokens[pc],
                )
            ####

            token = program.tokens[pc]
            word = token.text

            if is_number_token(word):
                self._push_finite(float(word), token)
                pc += 1
                continue
            ####

            if word == "+":
                left, right = self._pop_binary(token)
                self._push_finite(left + right, token)
                pc += 1
            elif word == "-":
                left, right = self._pop_binary(token)
                self._push_finite(left - right, token)
                pc += 1
            elif word == "*":
                left, right = self._pop_binary(token)
                self._push_finite(left * right, token)
                pc += 1
            elif word == "/":
                left, right = self._pop_binary(token)
                if right == 0.0:
                    raise JorthError("division by zero", token)
                ####
                self._push_finite(left / right, token)
                pc += 1
            elif word == "floor":
                self._push_finite(float(math.floor(self._pop(token))), token)
                pc += 1
            elif word == "dup":
                self._require_depth(1, token)
                self.stack.append(self.stack[-1])
                pc += 1
            elif word == "swap":
                self._require_depth(2, token)
                self.stack[-2], self.stack[-1] = self.stack[-1], self.stack[-2]
                pc += 1
            elif word == "drop":
                self._pop(token)
                pc += 1
            elif word == "=":
                left, right = self._pop_binary(token)
                self.stack.append(1.0 if left == right else 0.0)
                pc += 1
            elif word == "!=":
                left, right = self._pop_binary(token)
                self.stack.append(1.0 if left != right else 0.0)
                pc += 1
            elif word == ">":
                left, right = self._pop_binary(token)
                self.stack.append(1.0 if left > right else 0.0)
                pc += 1
            elif word == ">=":
                left, right = self._pop_binary(token)
                self.stack.append(1.0 if left >= right else 0.0)
                pc += 1
            elif word == "<":
                left, right = self._pop_binary(token)
                self.stack.append(1.0 if left < right else 0.0)
                pc += 1
            elif word == "<=":
                left, right = self._pop_binary(token)
                self.stack.append(1.0 if left <= right else 0.0)
                pc += 1
            elif word == "if":
                condition = self._pop(token)
                jump = program.if_false_jumps.get(pc)
                if jump is None:
                    raise JorthError("internal error: missing 'if' target", token)
                ####
                pc = jump if condition == 0.0 else pc + 1
            elif word == "def":
                jump = program.definition_jumps.get(pc)
                if jump is None:
                    raise JorthError("internal error: missing 'def' target", token)
                ####
                pc = jump
            elif word == "end":
                if pc in program.conditional_ends:
                    pc += 1
                elif pc in program.function_ends:
                    pc = self._return_from_function(token)
                else:
                    raise JorthError("internal error: unclassified 'end'", token)
                ####
            elif word == "ret":
                pc = self._return_from_function(token)
            elif word == "store":
                if pc + 1 >= len(program.tokens):
                    raise JorthError("'store' requires a variable name", token)
                ####
                name_token = program.tokens[pc + 1]
                self.variables[name_token.text] = self._pop(token)
                pc += 2
            elif word == "print":
                self.output(format_number(self._pop(token)))
                pc += 1
            elif word == "dump":
                rendered = ", ".join(format_number(value) for value in self.stack)
                self.output(f"[{rendered}]")
                pc += 1
            elif word in self.variables:
                self.stack.append(self.variables[word])
                pc += 1
            elif word in program.functions:
                function = program.functions[word]
                self.return_stack.append(pc + 1)
                pc = function.start
            else:
                raise JorthError(f"unknown word '{word}'", token)
            ####
        ####

        if self.return_stack:
            raise JorthError("program ended with unfinished function calls")
        ####

        return self.stack.copy()

    ####

    def _pop(self, token: Token) -> float:
        self._require_depth(1, token)
        return self.stack.pop()
    ####

    def _pop_binary(self, token: Token) -> tuple[float, float]:
        self._require_depth(2, token)
        right = self.stack.pop()
        left = self.stack.pop()
        return left, right

    ####

    def _require_depth(self, depth: int, token: Token) -> None:
        if len(self.stack) < depth:
            raise JorthError(
                f"stack underflow in '{token.text}': need {depth}, have {len(self.stack)}",
                token,
            )
        ####
    ####

    def _push_finite(self, value: float, token: Token) -> None:
        if not math.isfinite(value):
            raise JorthError(f"non-finite numeric result from '{token.text}'", token)
        ####
        self.stack.append(value)
    ####

    def _return_from_function(self, token: Token) -> int:
        if not self.return_stack:
            raise JorthError("'ret' is only valid inside a function", token)
        ####
        return self.return_stack.pop()
    ####
####


def run_file(path: Path, *, output: Output = print) -> list[float]:
    return JorthVM(output=output).run(path.read_text(encoding="utf-8"))
####


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print("usage: python jorth.py <filename>", file=sys.stderr)
        return 2
    ####

    path = Path(arguments[0])
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"jorth: cannot read '{path}': {error}", file=sys.stderr)
        return 2
    ####

    try:
        JorthVM().run(source)
    except JorthError as error:
        print(f"jorth: {error}", file=sys.stderr)
        return 1
    ####

    return 0


####


if __name__ == "__main__":
    raise SystemExit(main())
####
