"""Run the repository checks in the same order locally and in CI."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_PATHS = ("src", "scripts", "tests")
RUFF_PATHS = (*PYTHON_PATHS, "projects/scripts/altchar/tests")
SCOPE_MARKER_PATHS = (
    *PYTHON_PATHS,
    "projects/converging-flow/examples",
    "projects/scripts/altchar",
)


def ci_commands(
    python: str = sys.executable,
    *,
    fix: bool = False,
) -> tuple[tuple[str, ...], ...]:
    """Return ordered, platform-independent commands used by CI."""
    ruff = (python, "-m", "ruff", "check")
    scope_markers = (python, "-m", "scope_markers")
    rumdl = (python, "-m", "scripts.check_rumdl")
    commands: list[tuple[str, ...]] = [
        (python, "-m", "compileall", "-q", *PYTHON_PATHS),
    ]
    if fix:
        # Scope-marker insertion must happen after Ruff has finished editing.
        commands.extend(
            [
                (*ruff, "--fix", *RUFF_PATHS),
                (*scope_markers, "--fix", *SCOPE_MARKER_PATHS),
                (*rumdl, "--fix"),
            ]
        )
    ####
    commands.extend(
        [
            (*ruff, *RUFF_PATHS),
            (*scope_markers, *SCOPE_MARKER_PATHS),
            (python, "-m", "pytest", "-q"),
            (*rumdl,),
            (python, "-m", "mdrepo", "check", "."),
        ]
    )
    return tuple(commands)
####


def run_command(command: Sequence[str]) -> int:
    """Run one check from the repository root."""
    environment = os.environ.copy()
    cache = ROOT / ".tmp" / "cupy-cache"
    cache.mkdir(parents=True, exist_ok=True)
    environment.setdefault("CUPY_CACHE_DIR", str(cache.resolve()))
    source_path = str(ROOT / "src")
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        path for path in (source_path, existing_pythonpath) if path
    )
    try:
        completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    except OSError as error:
        print(f"CI command could not start: {' '.join(command)}: {error}", file=sys.stderr)
        return 1
    ####
    return completed.returncode
####


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the repository checks in CI order, stopping on failure."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="run Ruff and scope-markers autofixes before read-only checks",
    )
    arguments = parser.parse_args(argv)
    for command in ci_commands(fix=arguments.fix):
        print(f"$ {' '.join(command)}", flush=True)
        return_code = run_command(command)
        if return_code:
            return return_code
        ####
    ####
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
