"""Check that CI includes the article pilot and maintained examples."""

from scripts.ci import ci_commands


def test_check_commands_cover_pilot_and_examples() -> None:
    commands = ci_commands("python")
    assert (
        "python", "-m", "scope_markers", "src", "scripts", "tests",
        "projects/converging-flow/examples", "projects/scripts/altchar",
    ) in commands
    assert (
        "python", "-m", "ruff", "check", "src", "scripts", "tests",
        "projects/scripts/altchar/tests",
    ) in commands
####


def test_fix_commands_cover_the_same_explicit_paths() -> None:
    commands = ci_commands("python", fix=True)
    assert (
        "python", "-m", "scope_markers", "--fix", "src", "scripts", "tests",
        "projects/converging-flow/examples", "projects/scripts/altchar",
    ) in commands
    assert (
        "python", "-m", "ruff", "check", "--fix", "src", "scripts", "tests",
        "projects/scripts/altchar/tests",
    ) in commands
####
