# Notes

A small, durable note dump for procedures, references, decisions, troubleshooting, and other useful context.

## Organization

Use folders by subject area rather than by file type:

- `notes/<topic>/` — focused notes, procedures, and references
- `decisions/` — durable choices and their rationale
- `troubleshooting/` — symptoms, diagnosis, and fixes
- `inbox/` — unprocessed material that still needs a home

Create a new top-level folder only when a subject will have several related notes. Keep filenames lowercase, use hyphens, and make them descriptive enough to find with a quick directory search.

## Note conventions

Prefer Markdown. Start each note with:

```markdown
# Clear title

> Type: how-to | reference | decision | troubleshooting
> Status: current | superseded | needs-review
> Updated: YYYY-MM-DD
> Tags: example, topic-name
```

Use lowercase tags separated by a comma and one space; use hyphens within multiword tags. Choose a few stable subject terms, not a long list of synonyms. Search a complete tag from the repository root with:

```sh
rg -l '^> Tags: ([a-z0-9-]+, )*typography(,|$)' notes
```

Replace `typography` with the tag to find. `rg` searches note text as well; tags provide a consistent way to discover related subjects without requiring a generated index.

Then capture the purpose, prerequisites, procedure or findings, verification, and recovery/rollback details as relevant. Record environment-specific values explicitly, and separate them from reusable instructions. Link related notes instead of duplicating them.

## Browse by subject

### Graphic design

- [Graphic design terminology](notes/graphic-design/graphic-design-terminology.md) — logo, typography, and color guides

### Windows

- [Set Git Bash as the Windows Terminal default](notes/windows/windows-terminal-default-git-bash.md)
- [Shrink a WSL2 virtual disk](notes/windows/shrink-wsl2-vhdx.md)
