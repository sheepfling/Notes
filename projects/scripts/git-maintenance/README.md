# Git maintenance helpers

> Type: project note
> Status: needs-review; repository-changing
> Updated: 2026-08-02

This project contains helpers for finding Git repositories and applying conservative update
commands across them.

- [`find_and_pull_all_git.py`](find_and_pull_all_git.py) discovers normal and bare repositories
  and can issue fast-forward-only updates.
- [`find-and-pull-all-git.md`](find-and-pull-all-git.md) documents the discovery/update workflow.
- [`git-sync-service.md`](git-sync-service.md) records the scheduled-service idea.

Preview the target list from the repository root before updating anything:

```shell
python projects/scripts/git-maintenance/find_and_pull_all_git.py <search-root> --dry-run
```

The preview does not run Git or write a log. Discovery does not follow directory
symlinks and skips linked worktrees and submodules represented by a `.git` file.
It does discover nested ordinary repositories inside an ordinary worktree, so
review the entire target list. Choose a narrow search root: an actual update
fetches and prunes remote refs and then fast-forwards ordinary repositories,
which changes repository state.
The update command exits nonzero if any repository update fails or raises an
error; it continues processing the other discovered repositories and records
their outcomes in the log. A successful update or dry run exits zero.

Run the focused tests from the repository root:

```shell
python -m pytest projects/scripts/git-maintenance/tests
```

These tests create temporary directory fixtures and inspect generated commands; they do not run
fetch or pull. An actual update writes `git_update.log` under its search root. Bare repositories
are identified using their `HEAD`, `config`, `objects` and `refs` entries. Linked worktrees and
submodules represented by a `.git` file are intentionally excluded; update those separately.
