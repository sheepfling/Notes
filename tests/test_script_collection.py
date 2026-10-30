"""Compatibility entrypoint for the article-owned script tests.

The tests live beside their notes. This module preserves the historical
``python -m pytest tests/test_script_collection.py`` command while the
co-located test directories are also collected by the aggregate suite.
"""

import importlib.util
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "projects" / "scripts"
ARTICLE_TESTS = (
    "altchar/tests/test_altchar.py",
    "base64/tests/test_base64_article.py",
    "git-maintenance/tests/test_git_maintenance.py",
    "power-diagnostics/tests/test_power_diagnostics.py",
    "readlines/tests/test_readlines.py",
    "textball/tests/test_textball_article.py",
    "toy-ciphers/tests/test_toy_ciphers_article.py",
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
