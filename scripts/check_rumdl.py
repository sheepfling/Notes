"""Run rumdl against the maintained Markdown documentation roots."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

MARKDOWN_ROOTS = ("README.md", "notes", "projects")


def find_rumdl() -> str:
    """Find the rumdl executable in PATH or beside the active interpreter."""
    executable = shutil.which("rumdl")
    if executable:
        return executable
    ####
    interpreter_directory = Path(sys.executable).parent
    for name in ("rumdl.exe", "rumdl"):
        candidate = interpreter_directory / name
        if candidate.exists():
            return str(candidate)
        ####
    ####
    return "rumdl"
####


def main(argv: Sequence[str] | None = None) -> int:
    """Run rumdl, optionally applying its safe Markdown fixes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="apply rumdl fixes")
    arguments = parser.parse_args(argv)
    command = [find_rumdl(), "check"]
    if arguments.fix:
        command.append("--fix")
    ####
    command.extend(MARKDOWN_ROOTS)
    return subprocess.run(command, check=False).returncode
####


if __name__ == "__main__":
    raise SystemExit(main())
####
