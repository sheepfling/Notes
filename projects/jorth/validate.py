#!/usr/bin/env python3
"""Run shared conformance cases against the Python and JavaScript Jorth VMs."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class SuccessCase:
    name: str
    source: str
    expected_stdout: tuple[str, ...]
####


@dataclass(frozen=True, slots=True)
class ErrorCase:
    name: str
    source: str
    expected_error: str
####


SUCCESS_CASES: tuple[SuccessCase, ...] = (
    SuccessCase("arithmetic", "2 3 + 4 * print", ("20",)),
    SuccessCase(
        "operand-order",
        "10 3 - print 10 4 / print 2 3 < print 3 2 > print "
        "2 2 <= print 3 2 >= print",
        ("7", "2.5", "1", "1", "1", "1"),
    ),
    SuccessCase(
        "stack-words",
        "1 2 swap - print 8 dup * print 5 drop 3.9 floor print",
        ("1", "64", "3"),
    ),
    SuccessCase("variables", "42 store answer answer print", ("42",)),
    SuccessCase("function", "def square dup * end 7 square print", ("49",)),
    SuccessCase(
        "conditionals",
        "0 if 99 print end 1 if 5 print 1 if 6 print end end",
        ("5", "6"),
    ),
    SuccessCase(
        "recursion",
        "def fact dup 1 <= if drop 1 ret end dup 1 - fact * end "
        "5 fact print",
        ("120",),
    ),
    SuccessCase(
        "comments-whitespace",
        "# comment\n2\t3\n+ print # trailing comment\n",
        ("5",),
    ),
    SuccessCase(
        "forward-function-reference",
        "4 cube print def cube dup dup * * end",
        ("64",),
    ),
    SuccessCase("dump", "1 2 3 dump", ("[1, 2, 3]",)),
)

ERROR_CASES: tuple[ErrorCase, ...] = (
    ErrorCase("stack-underflow", "1 +", "stack underflow"),
    ErrorCase("unknown-word", "wat", "unknown word 'wat'"),
    ErrorCase("division-by-zero", "1 0 /", "division by zero"),
    ErrorCase("unclosed-if", "1 if 2", "unclosed 'if'"),
    ErrorCase("unmatched-end", "end", "unmatched 'end'"),
    ErrorCase("invalid-name", "def 123 1 end", "invalid word name '123'"),
    ErrorCase("ret-outside-function", "ret", "'ret' is only valid inside a function"),
    ErrorCase(
        "duplicate-function",
        "def f 1 end def f 2 end",
        "duplicate function 'f'",
    ),
    ErrorCase("reserved-variable", "1 store dup", "invalid word name 'dup'"),
)


def run_command(command: list[str], program_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*command, str(program_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
####


def lines(text: str) -> tuple[str, ...]:
    return tuple(line.rstrip() for line in text.splitlines())
####


def validate_success(
    case: SuccessCase,
    runners: dict[str, list[str]],
    directory: Path,
) -> list[str]:
    failures: list[str] = []
    program_path = directory / f"{case.name}.jorth"
    program_path.write_text(case.source, encoding="utf-8")

    for runner_name, command in runners.items():
        result = run_command(command, program_path)
        actual = lines(result.stdout)
        if result.returncode != 0:
            failures.append(
                f"{case.name}/{runner_name}: expected success, got exit "
                f"{result.returncode}: {result.stderr.strip()}"
            )
        elif actual != case.expected_stdout:
            failures.append(
                f"{case.name}/{runner_name}: expected {case.expected_stdout!r}, "
                f"got {actual!r}"
            )
        ####
    ####

    return failures
####


def validate_error(
    case: ErrorCase,
    runners: dict[str, list[str]],
    directory: Path,
) -> list[str]:
    failures: list[str] = []
    program_path = directory / f"error-{case.name}.jorth"
    program_path.write_text(case.source, encoding="utf-8")

    for runner_name, command in runners.items():
        result = run_command(command, program_path)
        if result.returncode == 0:
            failures.append(f"{case.name}/{runner_name}: expected failure, got success")
        elif case.expected_error not in result.stderr:
            failures.append(
                f"{case.name}/{runner_name}: expected stderr containing "
                f"{case.expected_error!r}, got {result.stderr.strip()!r}"
            )
        ####
    ####

    return failures
####


def main() -> int:
    node = shutil.which("node")
    if node is None:
        print("validation error: Node.js is not installed", file=sys.stderr)
        return 2
    ####

    runners = {
        "python": [sys.executable, str(ROOT / "jorth.py")],
        "javascript": [node, str(ROOT / "jorth.js")],
    }
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="jorth-validation-") as temp_dir:
        directory = Path(temp_dir)
        for case in SUCCESS_CASES:
            failures.extend(validate_success(case, runners, directory))
        ####
        for case in ERROR_CASES:
            failures.extend(validate_error(case, runners, directory))
        ####
    ####

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        ####
        return 1
    ####

    implementation_runs = 2 * (len(SUCCESS_CASES) + len(ERROR_CASES))
    print(
        f"PASS: {len(SUCCESS_CASES)} success cases and "
        f"{len(ERROR_CASES)} error cases across both implementations "
        f"({implementation_runs} interpreter runs)."
    )
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
