# Inserting and removing marker characters

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

[`altchar.py`](altchar.py) inserts a marker after each non-newline character and can later remove the same number of marker characters. It was intended for experimenting with text transformations that survive simple line-oriented handling.

The implementation preserves newline characters, streams input line by line, and exposes a built-in `test` action for the insert/remove cycle.

## Usage

Run the self-check:

```powershell
Set-Content -LiteralPath one-line.txt -Value 'abcd' -NoNewline
python altchar.py test one-line.txt --char A
```

The self-check now handles multi-line input: insertion skips newline characters and removal skips marker characters only after ordinary characters. Removal also checks that the expected marker is actually present instead of blindly discarding bytes.

Insert a marker, writing the default `.a` output:

```powershell
python altchar.py insert input.txt --char A
```

Remove it, writing the default `.rem` output:

```powershell
python altchar.py remove input.txt.a --char A
```

The transform is reversible only when the same marker string is used and the original text does not contain ambiguous marker sequences. It is text-only and is not compression, encryption, or a general binary-safe encoding.
