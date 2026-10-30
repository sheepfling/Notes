"""Tests for Git repository discovery and update command construction."""

import importlib.util
from pathlib import Path


def load_git_helper():
    path = Path(__file__).resolve().parents[1] / "find_and_pull_all_git.py"
    spec = importlib.util.spec_from_file_location("find_and_pull_all_git", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
####


def test_git_script_discovers_normal_and_bare_repositories(tmp_path: Path) -> None:
    module = load_git_helper()
    normal = tmp_path / "normal" / ".git"
    bare = tmp_path / "bare.git"
    normal.mkdir(parents=True)
    bare.mkdir()
    (bare / "config").write_text("[core]\n\tbare = true\n", encoding="utf-8")
    (bare / "head").write_text("ref: refs/heads/main\n", encoding="utf-8")

    found = set(module.find_git_repos(tmp_path))

    assert tmp_path / "normal" in found
    assert bare in found
####


def test_git_script_uses_non_destructive_update_commands(tmp_path: Path) -> None:
    module = load_git_helper()

    commands = module.update_commands(tmp_path / "repo", bare=False)

    assert [part for command in commands for part in command if part in {"reset", "clean", "checkout"}] == []
    assert commands[-1][-2:] == ["pull", "--ff-only"]
####
