# Clean up local Git branches after remote pruning

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

A local branch can outlive its remote branch. Pruning remote-tracking references makes the state
visible, but it does not delete local branches automatically. Review each candidate before
removing it.

## Refresh remote state

Run this from the repository whose branches you are reviewing:

```bash
git fetch --prune
git branch -vv
```

In the verbose branch listing, a tracking branch whose remote counterpart disappeared is marked
`[gone]`. A branch may also be intentionally local, so `[gone]` is a review signal, not a delete
command.

## Remove reviewed branches

First check the candidate’s commits and working-tree state:

```bash
git log --oneline --decorate --graph <branch-name> -n 20
git status --short
```

If the work is no longer needed and Git considers it merged, use the safe delete form:

```bash
git branch --delete <branch-name>
```

`--delete` refuses to remove a branch whose commits are not reachable from another local branch.
That refusal is useful: inspect the commits before deciding whether they are backed up elsewhere.

Only use force deletion when the branch is definitely disposable and its commits are preserved
somewhere else:

```bash
git branch --delete --force <branch-name>
```

Do not run a pipeline that automatically converts every `[gone]` branch into `--force` deletion.
Remote deletion can be intentional, temporary, or unrelated to the local work you still need.

## Verify

```bash
git branch --list
git status --short
git fsck --no-reflogs --unreachable
```

Unreachable commits may remain recoverable through `reflogs` for a while, but `reflogs` are not a
backup. Create a tag or a separate branch before deleting anything that may be useful.
