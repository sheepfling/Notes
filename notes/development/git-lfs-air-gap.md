# Git LFS and air-gapped copies

> Type: reference  
> Status: needs-review  
> Updated: 2026-08-01

Git LFS stores small pointer files in Git commits and keeps the corresponding large content in
an LFS object store. A working tree can contain the real files even though the commits still
contain pointers. That distinction is the important part of transferring an LFS repository.

The original note suggested that disabling the LFS filters turns pointer blobs into ordinary Git
blobs. It does not. Filter configuration changes checkout and staging behavior; it does not rewrite
existing commits or recover the large objects. The result can be a repository that appears to
contain files while actually containing pointer text.

## Connected checkout: materialize the working tree

On a machine with access to the LFS objects:

```
git lfs fetch --all
git lfs checkout
```

This downloads available LFS objects into the local cache and replaces pointer files in the
working tree with their contents. It does not change the Git history. The official FAQ describes
the pointer-file distinction and the role of `git lfs pull`/checkout in restoring working-tree
files: [Git LFS FAQ](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-faq.adoc).

## Choose the transfer goal

### Preserve history as normal Git blobs

Use `git lfs migrate export` in a disposable clone or a deliberately coordinated branch. It
rewrites history, changes commit IDs, and must be treated like any other history rewrite:

```
git lfs fetch --all
git lfs migrate export --everything --include="*.bin,*.dat"
git lfs checkout
```

Replace the patterns with the actual LFS-tracked paths. Review the rewritten history and verify
the current tree before pushing it to a new destination. Do not force-push the result over the
source repository without coordinating with every consumer.

`migrate export` does not simply delete every `.gitattributes` entry. The Git LFS documentation
says export adds non-LFS (“do not track”) rules, so inspect `.gitattributes` and adjust it for the
new repository if needed: [git-lfs-migrate](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-migrate.adoc).

Useful checks after migration:

```
git lfs ls-files
git grep -n -I "^version https://git-lfs.github.com/spec/v1" HEAD --
git status --short
```

For the exported paths, the first command should no longer report LFS tracking and the second
should find no pointer text in the current commit. Also inspect representative large files with
`file` or a checksum appropriate to the format.

### Keep only the current materialized snapshot

If history is not required, the simplest air-gapped import is often a new ordinary repository:

1. Fetch and check out the real LFS files on the connected machine.
2. Copy the working tree, excluding `.git`, into a new directory.
3. Run `git init`, add the files, and commit them as normal Git blobs.
4. Push or copy that new repository into the air-gapped environment.

This avoids rewriting the original history but intentionally does not preserve its commit graph,
branches, tags, or LFS metadata. Check the resulting repository size before committing large
datasets.

### Keep pointer files and fetch later

If the air-gapped copy only needs source history and does not need the large files yet, retain the
LFS metadata and skip automatic downloads:

```
git lfs install --skip-smudge
```

This deliberately leaves pointer files in the working tree. It is not a conversion to ordinary
Git, and it is not suitable for tools that need the actual file contents. The `GIT_LFS_SKIP_SMUDGE`
setting has the same narrow purpose; see [Git LFS configuration](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-config.adoc).

## What not to rely on

- Copying `.git/lfs/objects` preserves a local cache, but it does not make LFS pointers into Git
  blobs and does not create a usable remote by itself.
- Setting `filter.lfs.smudge` or `filter.lfs.clean` to `cat` can suppress filter work, but it can
  expose pointer text and does not convert history.
- `git format-patch` made from an unconverted LFS history describes the Git commits, which contain
  pointer blobs; it is not a reliable way to package the large LFS content for an air gap.
- A successful checkout is not proof that a commit contains normal Git blobs. Inspect the object
  type and pointer text explicitly.

## Validation checklist

- [ ] Decide whether history or only the current snapshot is required.
- [ ] Materialize and inspect the connected working tree.
- [ ] If preserving history, run migration in a disposable or coordinated clone.
- [ ] Inspect `.gitattributes` after migration.
- [ ] Search the current tree for LFS pointer headers.
- [ ] Test representative large files after transfer, including checksums where appropriate.
- [ ] Keep generated bundles and transfer media outside this notes repository; do not commit
  binaries or private infrastructure details here.
