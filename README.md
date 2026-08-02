# Notes

A small, durable note dump for procedures, references, decisions, troubleshooting, and other useful context.

## Browse by category

Notes live under `notes/`, grouped by subject rather than file type:

- [Aerospace](notes/aerospace/README.md) — flight dynamics and validation
- [Development](notes/development/README.md) — compilers, SDKs, and build tools
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

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The equivalent setup with uv is:

```powershell
uv sync --extra dev
```

Run all configured checks:

```powershell
uv run pytest
```

Validate local Markdown links, including repository containment and ignore rules:

```powershell
uv run python scripts/validate_notes.py
```

Check for machine-specific absolute paths and private IPv4 addresses. Placeholder paths such as
`C:\Users\<user>` and `/Users/REPLACE_ME` are allowed; pass any known private names or values at
runtime with `--forbidden` rather than writing them into the repository:

```powershell
uv run python scripts/check_scrubbed.py
```

Check HTTP(S) links for 404/410 responses as a separate network-dependent step:

```powershell
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

```powershell
python -m pytest
```

Add future Python test directories to `testpaths` and keep generated environments and caches out of version control. Generated Python outputs belong under the ignored `artifacts/` directory, not beside the notes or source.

## Collections

Collections can contain a README, scripts, source files, tests, and supporting notes. The directory itself is the durable record; use `NOTES.md` for provenance, caveats, and validation history.
