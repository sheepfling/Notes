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

Inspect the command construction and target root before running it. Even a fast-forward-only pull
changes repository state, and discovery across a broad directory can affect more repositories
than intended.

Run the focused tests from the repository root:

```shell
python -m pytest projects/scripts/git-maintenance/tests
```

These tests create temporary directory fixtures and inspect generated commands; they do not run
fetch or pull. The updater itself writes `git_update.log` under its search root. Its current bare
repository discovery checks for a lowercase `head` file, so it can miss normal bare repositories
on case-sensitive filesystems; it also does not discover linked worktrees represented by a `.git`
file. Review its target list and output location before using it.
