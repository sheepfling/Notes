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
