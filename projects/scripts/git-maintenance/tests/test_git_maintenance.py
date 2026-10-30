"""Tests for Git repository discovery and update command construction."""

import importlib.util
import sys
from pathlib import Path

import pytest


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
    (bare / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (bare / "objects").mkdir()
    (bare / "refs").mkdir()

    found = set(module.find_git_repos(tmp_path))

    assert tmp_path / "normal" in found
    assert bare in found
    assert list(module.find_git_repos(bare)) == [bare]
####


def test_discovery_skips_linked_worktrees_and_directory_symlinks(tmp_path: Path) -> None:
    module = load_git_helper()
    root = tmp_path / "workspace"
    root.mkdir()
    ordinary = root / "ordinary"
    (ordinary / ".git").mkdir(parents=True)
    nested_ordinary = ordinary / "nested"
    (nested_ordinary / ".git").mkdir(parents=True)
    linked = root / "linked"
    linked.mkdir()
    (linked / ".git").write_text("gitdir: /placeholder/worktree\n", encoding="utf-8")
    (linked / "nested" / ".git").mkdir(parents=True)
    outside = tmp_path / "outside"
    (outside / "remote" / ".git").mkdir(parents=True)
    try:
        (root / "outside-link").symlink_to(outside, target_is_directory=True)
        (root / "loop").symlink_to(root, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlinks unavailable: {error}")
    ####

    assert set(module.find_git_repos(root)) == {ordinary, nested_ordinary}
    assert set(module.find_git_repos_semi_random(root)) == {ordinary, nested_ordinary}
    assert set(module.find_git_repos(ordinary)) == {ordinary, nested_ordinary}
####


def test_dry_run_lists_targets_without_git_or_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_git_helper()
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setattr(sys, "argv", ["find_and_pull_all_git.py", str(tmp_path), "--dry-run"])
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: pytest.fail("Git was invoked"))
    module.main()
    assert capsys.readouterr().out.splitlines() == [str(repo)]
    assert not (tmp_path / "git_update.log").exists()
####


def test_git_script_uses_non_destructive_update_commands(tmp_path: Path) -> None:
    module = load_git_helper()

    commands = module.update_commands(tmp_path / "repo", bare=False)

    assert [part for command in commands for part in command if part in {"reset", "clean", "checkout"}] == []
    assert commands[-1][-2:] == ["pull", "--ff-only"]
####
