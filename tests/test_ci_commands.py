"""Check that article tests and maintained examples participate in CI."""

import tomllib
from pathlib import Path

from scripts.ci import ci_commands

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_TEST_PATHS = {
    "notes/thermal/tests",
    "projects/scripts/altchar/tests",
    "projects/scripts/base64/tests",
    "projects/scripts/git-maintenance/tests",
    "projects/scripts/power-diagnostics/tests",
    "projects/scripts/readlines/tests",
    "projects/scripts/textball/tests",
    "projects/scripts/toy-ciphers/tests",
    "projects/scripts/transfer-bundle/tests",
    "projects/jorth/tests",
    "projects/integer-semantics-lab/tests",
    "projects/shaders/tests",
    "projects/converging-flow/examples/physics_diagnostics/tests",
    "projects/converging-flow/examples/backend_agnostic/tests",
}
SCOPE_PATHS = {
    "src", "scripts", "tests", "notes/thermal", "notes/quaternions/benchmark", "projects/converging-flow/examples",
    "projects/scripts", "projects/jorth", "projects/integer-semantics-lab", "projects/shaders/tests",
}


def test_article_tests_are_discovered_and_linted() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert ARTICLE_TEST_PATHS <= set(config["tool"]["pytest"]["ini_options"]["testpaths"])
    commands = ci_commands("python")
    ruff = next(command for command in commands if command[:4] == ("python", "-m", "ruff", "check"))
    assert ARTICLE_TEST_PATHS <= set(ruff)
    assert {"notes/thermal", "notes/quaternions/benchmark", "projects/scripts/toy-ciphers"} <= set(ruff)
####


def test_check_and_fix_commands_cover_the_same_scope() -> None:
    check_commands = ci_commands("python")
    fix_commands = ci_commands("python", fix=True)
    check = next(command for command in check_commands if command[:3] == ("python", "-m", "scope_markers"))
    fix = next(command for command in fix_commands if command[:4] == ("python", "-m", "scope_markers", "--fix"))
    assert SCOPE_PATHS <= set(check)
    assert set(check[3:]) == set(fix[4:])
    ruff_fix = next(command for command in fix_commands if command[:5] == ("python", "-m", "ruff", "check", "--fix"))
    assert ARTICLE_TEST_PATHS <= set(ruff_fix)
    assert ("python", "-m", "compileall", "-q", "src", "scripts", "tests") in check_commands
####
