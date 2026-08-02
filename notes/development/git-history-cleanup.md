# Removing large or sensitive files from Git history

> Type: reference  
> Status: historical  
> Updated: 2026-08-01

The old notes used the BFG Repo-Cleaner to remove oversized blobs from a repository. This is a
history rewrite, not a working-tree cleanup. It changes commit IDs and can affect every clone,
branch, tag, pull request, and deployment that contains the rewritten history.

## Before rewriting anything

1. Make a disposable mirror clone or a verified backup.
2. Identify the exact paths or blob-size rule to remove.
3. Decide whether the data is merely inconveniently large or genuinely secret. If it is secret,
   revoke or rotate the credential first; rewriting history does not undo a leak.
4. Coordinate the replacement history with everyone who consumes the repository.
5. Keep the cleaner JAR, temporary clones, and generated reports outside this Notes repository.

## BFG outline

Install a supported Java runtime and download BFG from its
[official project page](https://rtyley.github.io/bfg-repo-cleaner/). Verify the download using a
trusted checksum or release source. The exact BFG version should be chosen deliberately; the
version in an old command is not a repository requirement.

Run BFG against a disposable mirror clone. For example, this removes blobs larger than 3 MiB:

```bash
java -jar /path/to/bfg.jar --strip-blobs-bigger-than 3M /path/to/repository.git
```

Review BFG’s report and the resulting refs before finalizing the clone. The command is intentionally
shown with generic paths and does not include a JAR or a repository copy.

## Expire unreachable objects

Only after reviewing the rewritten result, expire `reflogs` and repack the disposable clone:

```bash
cd /path/to/repository.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

Inspect the repository before publishing it:

```bash
git fsck --full --no-reflogs
git log --all --stat
git status --short
```

If the repository contains sensitive material, inspect all refs and confirm that the affected
content is absent. Existing clones and caches may still retain the old objects, so communicate
the cleanup and require fresh clones or coordinated ref updates as appropriate.

## Safer alternatives

If the goal is only to reduce a local checkout, delete or move files in the working tree and
commit normally. If the goal is a repeatable modern history rewrite, evaluate a maintained
history-rewrite tool and document the exact path filters and verification checks before running
it. Never use `reset --hard` or `git clean` as a substitute for removing content from history;
those commands affect a worktree, not other commits or clones.
