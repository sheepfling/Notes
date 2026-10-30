# Finding and updating many Git repositories

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

The script [find_and_pull_all_git.py](find_and_pull_all_git.py) walks a directory tree, recognizes ordinary and bare Git repositories, and updates them in parallel. It was meant for a workspace containing many small repositories that otherwise had to be visited one by one.

## What it does

For a normal working tree it fetches tags and prunes stale remote references, then runs
`git pull --ff-only`. It does not reset, clean, or switch branches.

Bare repositories receive a fetch of all remotes, tags, and pruned references. The script writes a `git_update.log` in the searched directory and offers a worker-count option.
It attempts all discovered targets and exits nonzero if any update fails or
raises an error; inspect the log for the affected repositories.

## Important warning

This is not a harmless “pull everything” command: fetching and pruning changes remote-tracking
references, and a successful fast-forward changes the checked-out branch. Earlier historical
versions used reset, clean, branch switching and duplicate update passes; the current sequence
does not. It intentionally skips directory symlinks and linked worktrees or submodules whose
`.git` entry is a file. Nested ordinary repositories inside an ordinary worktree remain separate
targets, so inspect the entire preview before updating.

First preview the targets without running Git or creating a log:

```shell
python projects/scripts/git-maintenance/find_and_pull_all_git.py <search-root> --dry-run
```

## Updating a small, reviewed root

```powershell
python projects/scripts/git-maintenance/find_and_pull_all_git.py C:\path\to\workspace --stdout --num-workers 4
```

Use a disposable test tree first. Do not point it at a home directory or a workspace containing uncommitted work.
