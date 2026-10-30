"""Compatibility entrypoint for the historical script-collection command.

Canonical tests are collected individually from ``tests/scripts``.
"""

import importlib.util
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent / "scripts"
ARTICLE_TESTS = (
    "test_altchar.py",
    "test_base64_article.py",
    "test_git_maintenance.py",
    "test_power_diagnostics.py",
    "test_readlines.py",
    "test_textball_article.py",
    "test_toy_ciphers_article.py",
)


def _forward_tests(relative_path: str) -> None:
    path = SCRIPT_ROOT / relative_path
    name = "article_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, value in vars(module).items():
        if name.startswith("test_"):
            if name in globals():
                raise RuntimeError(f"duplicate article test name: {name}")
            ####
            globals()[name] = value
        ####
    ####
####


for article_test in ARTICLE_TESTS:
    _forward_tests(article_test)
####
