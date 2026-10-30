"""Compatibility entry point for the shared test suite."""

import runpy
from pathlib import Path

_root = next(path for path in Path(__file__).resolve().parents if (path / "pyproject.toml").is_file())
_tests = runpy.run_path(str(_root / "tests/test_integer_semantics.py"))
globals().update({name: value for name, value in _tests.items() if name.startswith("test_")})
