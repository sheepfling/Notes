# Script projects

> Type: project index
> Status: needs-review
> Updated: 2026-08-02

This directory contains several small, independent experiments that were previously mixed
together in one script bucket. Each family now has its own directory, implementation notes,
and safety boundary.

| Project | Contents | Boundary |
|---|---|---|
| [transfer-bundle](transfer-bundle/README.md) | `tar.exe`, hashing, and complete Windows transfer bundles | Windows built-ins; inspect archives |
| [base64](base64/README.md) | Python and `certutil.exe` Base64 conversion | Encoding, not encryption |
| [textball](textball/README.md) | Text-only directory packaging and legacy extractor | Trusted input only |
| [altchar](altchar/README.md) | Reversible marker-character experiment | Text-only transform |
| [toy-ciphers](toy-ciphers/README.md) | OTP-shaped and repeating-passphrase experiments | Not cryptography |
| [git-maintenance](git-maintenance/README.md) | Repository discovery and update helpers | Can change repositories |
| [readlines](readlines/README.md) | Line-ending inspection helper | Diagnostic utility |
| [power-diagnostics](power-diagnostics/README.md) | Sleep, wake, reboot, and report generation | Read-only Windows diagnostics |

The Windows batch files live beside the Python or archive workflow they support. This makes the
fallback path discoverable without presenting all batch files as one unrelated toolkit.

Maintained Python article implementations are in `src/notes_tools/articles/`.
The documented historical Python script paths remain compatibility entry points
and locate the shared source when run from this checkout. To use an installed
module such as `python -m notes_tools.articles.altchar`, install the root project
first; the `scripts` extra supplies pytest for the focused tests:

```shell
python -m pip install -e ".[scripts]"
```

Run the focused tests from the repository root:

```
python -m pytest tests/scripts tests/test_batch_collection.py
```
