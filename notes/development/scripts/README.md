# Small script collection

> Type: collection note  
> Status: needs-review  
> Updated: 2026-08-01

These are reusable scripts extracted from an older personal notes project. Each script is kept beside a short blog-style explanation so the code retains its original context, limits, and lessons learned.

## First mature pass

| Script                                               | What it explores                                   | Status                                       |
|------------------------------------------------------|----------------------------------------------------|----------------------------------------------|
| [find_and_pull_all_git.py](find_and_pull_all_git.py) | Discover and update many Git repositories          | needs-review; destructive                    |
| [`textball.py`](textball.py)                         | Store a directory as a line-oriented text package  | needs-review; inspect before untrusted input |
| [`altchar.py`](altchar.py)                           | Insert and remove marker characters from text      | needs-review; text-only                      |
| [base64_cli.py](base64_cli.py)                       | Encode and decode files with Base64                | needs-review; not encryption                 |
| [otp.py](otp.py) and [pcrypt.py](pcrypt.py)          | Reversible printable-text cipher experiments       | needs-review; not cryptography               |
| [`readlines.py`](readlines.py)                       | Show line numbers and escaped line contents        | needs-review; diagnostic helper              |
| [git-sync-service.md](git-sync-service.md)           | Schedule conservative recursive Git updates        | needs-review; changes repositories           |
| [batch/](batch/README.md)                            | Windows-only tar, Base64, hash, and text fallbacks | needs-review; `cmd.exe` limits apply         |

Read the commentary before running any script. These are useful experiments and personal tools, not automatically production-ready utilities.

## Validation

The repository test suite exercises safe round trips for Base64, `textball`, the alternate-character
transform, both toy ciphers, the line-display helper, and non-destructive Git repository discovery.

From the repository root:

```powershell
uv run pytest tests/test_script_collection.py
```

## Later candidates

The source collection also contains unfinished batch files and scratch visualization code. Those
should get separate explanations and explicit safety labels before being treated as reusable notes.
