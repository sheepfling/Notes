# Notes

A small, durable note dump for procedures, references, decisions, troubleshooting, and other useful context.

## Browse by category

Notes live under `notes/`, grouped by subject rather than file type:

- [Aerospace](notes/aerospace/README.md) — flight dynamics and validation
- [Development](notes/development/README.md) — compilers, SDKs, and build tools
- [Projects](projects/README.md) — runnable and preserved source collections
- [Converging Flow](projects/converging-flow/README.md) — vectorized inert-flow, reactive-Euler,
  reaction-diffusion, and heterogeneous-wave simulations with reproducible artifacts
- [Windows](notes/windows/README.md) — Windows, WSL, and desktop procedures
- [References](notes/references/README.md) — curated link archives and reading queues

Material imported from other note collections should be reviewed and shaped into a durable note
or collection before it is committed. A local `inbox/` directory may be used as a temporary
ingestion scratchpad, but it is intentionally ignored and is not part of the published notes.

Add new notes to the appropriate category directory. This README intentionally links to categories instead of listing every note, so adding or renaming a note does not require an index edit. Create a new category only when a subject has several related notes.

## Note conventions

Prefer Markdown. Start each note with:

```markdown
# Clear title

> Type: how-to | reference | decision | troubleshooting
> Status: current | historical | superseded | needs-review
> Updated: YYYY-MM-DD
```

Then capture the purpose, prerequisites, procedure or findings, verification, and recovery/rollback details as relevant. Record environment-specific values explicitly, and separate them from reusable instructions. Link related notes instead of duplicating them.

Keep general command examples console-neutral when possible. Use `shell` or
unlabeled one-line fences for commands that work in both Bash-like shells and PowerShell;
reserve `bash`, `powershell`, and similar labels for shell-specific syntax.
See [console-neutral command examples](notes/development/markdown-console-conventions.md).

Use `current` for guidance that is intended to remain usable, `historical` for preserved material
that depends on an older tool or event, `superseded` when another note replaces it, and
`needs-review` when the material is useful but has not been recently revalidated.

## Finding a note

Use the category directories above, or search filenames and note contents from the repository root. For example, in PowerShell:

```powershell
Get-ChildItem -Path notes -Recurse -File |
    Select-String -Pattern 'search term'
```

Keep filenames lowercase, use hyphens, and make them descriptive enough to find with a quick directory search.

## Validation

The repository is primarily Markdown, but source collections can have optional automated checks. Python tooling is declared in `pyproject.toml`; it is not required to read or edit notes.

Set up a development virtual environment with pip:

```
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Activate it using the shell-specific command for your environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
source .venv/bin/activate
```

The equivalent setup with uv is:

```
uv sync --extra dev
```

Run all configured checks:

```
python -m scripts.ci
```

The local autofix sequence is deliberately ordered: Ruff fixes first,
scope-markers inserts/regenerates structural markers, and rumdl applies safe
Markdown fixes. The same checks then run read-only afterward:

```
python -m scripts.ci --fix
```

The CI workflow runs the read-only form. Rumdl checks `README.md`, `notes/`,
and `projects/` using the repository's relaxed-project policy in
`.rumdl.toml`; generated files and the intentionally scratch `inbox/` are
excluded. CI then runs `mdrepo check .` for repository-wide Markdown path,
case, and reachability policy. `mdrepo` leaves orphan detection disabled for
the historical note dump; link and path checks remain active.

With uv, the equivalent command is `uv run pytest`.

Validate local Markdown links, including repository containment and ignore rules:

```
uv run python scripts/validate_notes.py
```

Check for machine-specific absolute paths and private IPv4 addresses. Placeholder paths such as
`C:\Users\<user>` and `/Users/REPLACE_ME` are allowed; pass any known private names or values at
runtime with `--forbidden` rather than writing them into the repository:

```
uv run python scripts/check_scrubbed.py
```

Check HTTP(S) links for 404/410 responses as a separate network-dependent step:

```
uv run python scripts/validate_notes.py --external
```

## Source hygiene

When promoting material from an external collection, remove personal absolute paths, usernames,
employer or project identifiers, internal URLs, private IP addresses, credentials, generated
dumps, and binary artifacts. Use generic placeholders such as `<project-root>`,
`%USERPROFILE%`, or `/Users/REPLACE_ME` when the shape of a procedure matters. Keep generated
reports, plots, decoded files, package caches, and archives outside the repository or under the
ignored `artifacts/` directory. Run `check_scrubbed.py` with any known private values supplied
at runtime rather than recording those values in the repository.

When the dependencies are already installed in the active Python environment, the direct equivalent is:

```
python -m pytest
```

Measure Python line and branch coverage, including Python tools launched by the tests as subprocesses:

```
python -m pytest --cov --cov-report=term-missing
```

The configured report threshold is an initial 45 percent floor. Batch files are covered by their
behavioral tests; Python coverage tools do not measure `.bat` source lines.

Add future Python test directories to `testpaths` and keep generated environments and caches out of version control. Generated Python outputs belong under the ignored `artifacts/` directory, not beside the notes or source.

## Collections

Collections can contain a README, scripts, source files, tests, and supporting notes. The directory itself is the durable record; use `NOTES.md` for provenance, caveats, and validation history.
