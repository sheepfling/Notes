from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JORTH_PATH = PROJECT_ROOT / "jorth.py"
VALIDATE_PATH = PROJECT_ROOT / "validate.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
####


jorth = load_module("jorth_under_test", JORTH_PATH)
validate = load_module("jorth_validate_under_test", VALIDATE_PATH)


def test_tokenize_and_scalar_helpers() -> None:
    tokens = jorth.tokenize("  12 # ignored\n\n +\t3.5e1")

    assert [(token.text, token.line, token.column) for token in tokens] == [
        ("12", 1, 3),
        ("+", 3, 2),
        ("3.5e1", 3, 4),
    ]
    assert jorth.is_number_token("-1.25")
    assert not jorth.is_number_token("1.2.3")
    assert jorth.format_number(-0.0) == "0"
    assert jorth.format_number(4.0) == "4"
    assert jorth.format_number(4.5) == "4.5"
####


def test_compile_records_conditionals_and_functions() -> None:
    program = jorth.compile_source("def square dup * end 0 if 1 end 4 square")

    assert program.functions["square"] == jorth.Function(start=2, end=4)
    assert program.if_false_jumps == {6: 9}
    assert program.definition_jumps == {0: 5}
    assert program.conditional_ends == frozenset({8})
    assert program.function_ends == frozenset({4})
####


def test_vm_arithmetic_stack_words_comparisons_and_output() -> None:
    output: list[str] = []
    vm = jorth.JorthVM(output=output.append)

    stack = vm.run(
        "10 3 - print 10 4 / print 2 3 = print 2 3 != print "
        "2 3 < print 3 2 > print 2 2 <= print 3 2 >= print"
    )

    assert stack == []
    assert output == ["7", "2.5", "0", "1", "1", "1", "1", "1"]
    assert vm.run("1 2 swap - 8 dup * 5 drop 3.9 floor") == [1.0, 64.0, 3.0]
####


def test_vm_variables_functions_conditionals_recursion_and_dump() -> None:
    output: list[str] = []
    vm = jorth.JorthVM(output=output.append)

    assert vm.run("42 store answer answer") == [42.0]
    assert vm.run("def square dup * end 7 square") == [49.0]
    assert vm.run("0 if 99 print end 1 if 5 print end") == []
    assert vm.run("def fact dup 1 <= if drop 1 ret end dup 1 - fact * end 5 fact") == [120.0]
    assert vm.run("1 2 3 dump") == [1.0, 2.0, 3.0]
    assert output == ["5", "[1, 2, 3]"]
####


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("1 +", "stack underflow"),
        ("1 0 /", "division by zero"),
        ("wat", "unknown word 'wat'"),
        ("1e309", "non-finite numeric result"),
        ("1 if 2", "unclosed 'if'"),
        ("def f 1", "unclosed 'def'"),
        ("end", "unmatched 'end'"),
        ("ret", "'ret' is only valid inside a function"),
        ("def 123 1 end", "invalid word name '123'"),
        ("def f 1 end def f 2 end", "duplicate function 'f'"),
        ("1 store dup", "invalid word name 'dup'"),
        ("if def f 1 end end", "'def' is only valid at top level"),
        ("store", "'store' requires a variable name"),
        ("1 store f def f 1 end", "variable 'f' conflicts with a function"),
    ],
)
def test_compile_and_runtime_errors(source: str, message: str) -> None:
    with pytest.raises(jorth.JorthError, match=re.escape(message)):
        jorth.JorthVM().run(source)
    ####
####


def test_vm_limits_and_word_validation() -> None:
    with pytest.raises(ValueError, match="max_steps must be positive"):
        jorth.JorthVM(max_steps=0)
    ####

    with pytest.raises(jorth.JorthError, match="step limit exceeded"):
        jorth.JorthVM(max_steps=2).run("1 2 3")
    ####

    jorth.validate_word_name(jorth.Token("valid_name-1", 2, 4))
    with pytest.raises(jorth.JorthError, match="invalid word name"):
        jorth.validate_word_name(jorth.Token("bad.name", 2, 4))
    ####
####


def test_run_file_and_cli_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    program = tmp_path / "program.jorth"
    program.write_text("2 3 + print", encoding="utf-8")
    output: list[str] = []

    assert jorth.run_file(program, output=output.append) == []
    assert output == ["5"]
    assert jorth.main([]) == 2
    assert "usage:" in capsys.readouterr().err
    assert jorth.main([str(tmp_path / "missing.jorth")]) == 2
    assert "cannot read" in capsys.readouterr().err
    assert jorth.main([str(program)]) == 0
    assert capsys.readouterr().out == "5\n"

    invalid = tmp_path / "invalid.jorth"
    invalid.write_text("wat", encoding="utf-8")
    assert jorth.main([str(invalid)]) == 1
    assert "unknown word 'wat'" in capsys.readouterr().err
####


def test_jorth_validation_helpers_and_case_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = [sys.executable, "-c", "print('ok')"]
    result = validate.run_command(command, tmp_path / "program.jorth")
    assert result.returncode == 0
    assert validate.lines(result.stdout) == ("ok",)
    assert validate.lines("one\nlast\n") == ("one", "last")

    runners = {"fake": ["fake"]}
    success = validate.SuccessCase("success", "1", ("ok",))
    error = validate.ErrorCase("error", "wat", "boom")

    monkeypatch.setattr(
        validate,
        "run_command",
        lambda _command, _path: subprocess.CompletedProcess(
            _command,
            0,
            stdout="ok\n",
            stderr="",
        ),
    )
    assert validate.validate_success(success, runners, tmp_path) == []
    assert validate.validate_error(error, runners, tmp_path) == [
        "error/fake: expected failure, got success"
    ]

    monkeypatch.setattr(
        validate,
        "run_command",
        lambda _command, _path: subprocess.CompletedProcess(
            _command,
            1,
            stdout="wrong\n",
            stderr="missing expected text",
        ),
    )
    assert validate.validate_success(success, runners, tmp_path)[0].startswith(
        "success/fake: expected success"
    )
    assert validate.validate_error(error, runners, tmp_path)[0].startswith(
        "error/fake: expected stderr"
    )
####


def test_jorth_validation_main_handles_missing_node_and_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(validate.shutil, "which", lambda _name: None)
    assert validate.main() == 2
    assert "Node.js is not installed" in capsys.readouterr().err

    success = validate.SuccessCase("success", "1", ("ok",))
    error = validate.ErrorCase("error", "wat", "boom")
    monkeypatch.setattr(validate, "SUCCESS_CASES", (success,))
    monkeypatch.setattr(validate, "ERROR_CASES", (error,))
    monkeypatch.setattr(validate.shutil, "which", lambda _name: "node")

    def passing_runner(command, program_path):
        if program_path.name.startswith("error-"):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="boom")
        ####
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")
    ####

    monkeypatch.setattr(validate, "run_command", passing_runner)
    assert validate.main() == 0
    assert "PASS: 1 success cases and 1 error cases" in capsys.readouterr().out

    failing_success = validate.SuccessCase("failure", "1", ("expected",))
    monkeypatch.setattr(validate, "SUCCESS_CASES", (failing_success,))
    monkeypatch.setattr(validate, "ERROR_CASES", ())
    monkeypatch.setattr(
        validate,
        "run_command",
        lambda command, _path: subprocess.CompletedProcess(
            command,
            0,
            stdout="wrong\n",
            stderr="",
        ),
    )
    assert validate.main() == 1
    assert "FAIL: failure/" in capsys.readouterr().err
####
