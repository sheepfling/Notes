"""Compatibility entry point for the shared test suite."""

import runpy
from pathlib import Path

_root = next(path for path in Path(__file__).resolve().parents if (path / "pyproject.toml").is_file())
_tests = runpy.run_path(str(_root / "tests/scripts/test_textball_creation_safety.py"))
globals().update({name: value for name, value in _tests.items() if name.startswith("test_")})
