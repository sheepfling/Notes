# Notes

A small, durable note dump for procedures, references, decisions,
troubleshooting, and other useful context.

## Organization

Use folders by subject area rather than by file type:

- `notes/<topic>/` — focused notes, procedures, and references
- `decisions/` — durable choices and their rationale
- `troubleshooting/` — symptoms, diagnosis, and fixes
- `inbox/` — unprocessed material that still needs a home

Create a new top-level folder only when a subject will have several related
notes. Keep filenames lowercase, use hyphens, and make them descriptive enough
to find with a quick directory search.

## Note conventions

Prefer Markdown. Start each note with:

```markdown
# Clear title

> Type: how-to | reference | decision | troubleshooting
> Status: current | superseded | needs-review
> Updated: YYYY-MM-DD
> Tags: example, topic-name
```

Use a few lowercase, hyphenated tags separated by a comma and one space. Tags
identify subjects across folders; use the type and status fields for the kind
and currency of a note.

Then capture the purpose, prerequisites, procedure or findings, verification,
and recovery/rollback details as relevant. Record environment-specific values
explicitly, and separate them from reusable instructions. Link related notes
instead of duplicating them.

## Tests for notes and experiments

Place automated tests for notes and their supporting code under
`tests/<topic>/`, separate from the note and its implementation. Use pytest
for Python tests, and make supporting Python code importable as a module.
Document the dependencies and repository-root commands needed to reproduce an
experiment and run its tests in the note itself.

## Find a note

Browse by subject below, or search from the repository root:

```shell
rg --files notes -g '*.md'                       # list notes
rg -n -i 'cooling' notes                         # search note contents
rg -l '^> Type: reference$' notes                # find notes by type
rg -l '^> Tags: ([a-z0-9-]+, )*thermal(,|$)' notes  # find an exact tag
```

Replace the example terms with the subject, type, or tag you need. The index
points to subject entry points; add related notes beneath each subject instead
of maintaining a single undifferentiated list.

## Browse by subject

### Quaternions

- [Quaternion performance in Python](notes/quaternions/quaternion-performance.md)
  — six-way benchmark and reproduction

### Thermal

- [Should You Add Creamer Now or Later?](notes/thermal/coffee-choice-problem.md)
  — cooling and mixing comparison

### Windows

The earlier index listed notes about setting Git Bash as the Windows Terminal
default and shrinking a WSL2 virtual disk, but those files are not present in
this branch.
