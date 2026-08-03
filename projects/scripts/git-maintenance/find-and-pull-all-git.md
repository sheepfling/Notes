# Finding and updating many Git repositories

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

The script [find_and_pull_all_git.py](find_and_pull_all_git.py) walks a directory tree, recognizes ordinary and bare Git repositories, and updates them in parallel. It was meant for a workspace containing many small repositories that otherwise had to be visited one by one.

## What it does

For a normal working tree it attempts to:

1. discard tracked changes with `git reset --hard`;
2. delete untracked files with `git clean -fd`;
3. check out `master`;
4. fetch tags and prune stale references; and
5. fast-forward with `git pull --ff-only`.

Bare repositories receive a fetch of all remotes, tags, and pruned references. The script writes a `git_update.log` in the searched directory and offers a worker-count option.

## Important warning

This is not a harmless “pull everything” command. The reset and clean steps can destroy local work, and forcing `master` makes assumptions about branch names and repository policy. The current script also contains both an initial sequential update pass and a later parallel pass, so it may update repositories twice.

Treat it as historical code until those behaviors are deliberately redesigned. A safer future version would default to read-only discovery, require an explicit destructive flag, preserve the current branch, use `git status` before changing anything, and support a dry run.

## Original usage shape

```powershell
python find_and_pull_all_git.py C:\path\to\workspace --stdout --num-workers 4
```

Use a disposable test tree first. Do not point it at a home directory or a workspace containing uncommitted work.
