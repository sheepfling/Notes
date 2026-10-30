"""Tests for Git repository discovery and update command construction."""

import importlib.util
import subprocess
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
    assert module.main() == 0
    assert capsys.readouterr().out.splitlines() == [str(repo)]
    assert not (tmp_path / "git_update.log").exists()
####


def test_git_script_uses_non_destructive_update_commands(tmp_path: Path) -> None:
    module = load_git_helper()

    commands = module.update_commands(tmp_path / "repo", bare=False)

    assert [part for command in commands for part in command if part in {"reset", "clean", "checkout"}] == []
    assert commands[-1][-2:] == ["pull", "--ff-only"]
####


def test_empty_search_is_successful(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_git_helper()
    monkeypatch.setattr(sys, "argv", ["find_and_pull_all_git.py", str(tmp_path)])
    monkeypatch.setattr(module, "update_repo", lambda _repo: pytest.fail("unexpected update"))
    assert module.main() == 0
####


@pytest.mark.parametrize("outcome", ["success", "failed", "exception"])
def test_update_status_reports_any_failed_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    module = load_git_helper()
    repos = [tmp_path / "first", tmp_path / "second"]
    visited: list[Path] = []

    def fake_update(repo: Path) -> bool:
        visited.append(repo)
        if repo == repos[0] and outcome == "exception":
            raise RuntimeError("simulated update failure")
        ####
        return repo != repos[0] or outcome != "failed"
    ####

    monkeypatch.setattr(sys, "argv", ["find_and_pull_all_git.py", str(tmp_path)])
    monkeypatch.setattr(module, "find_git_repos_semi_random", lambda _root: iter(repos))
    monkeypatch.setattr(module, "update_repo", fake_update)

    assert module.main() == (0 if outcome == "success" else 1)
    assert set(visited) == set(repos)
####


def test_failed_worker_propagates_cli_exit_status(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "find_and_pull_all_git.py"
    harness = """
import runpy
import sys
from pathlib import Path

namespace = runpy.run_path(sys.argv[1], run_name="git_helper_test")
main = namespace["main"]
main.__globals__["find_git_repos_semi_random"] = lambda root: iter([root / "mock-repo"])
main.__globals__["update_repo"] = lambda _repo: False
sys.argv = [sys.argv[1], str(Path(sys.argv[2]))]
raise SystemExit(main())
"""
    result = subprocess.run(
        [sys.executable, "-c", harness, str(script), str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
####
