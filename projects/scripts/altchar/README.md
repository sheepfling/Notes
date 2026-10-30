# Inserting and removing marker characters

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

[`altchar.py`](altchar.py) inserts a marker after each non-newline character and can later remove the same number of marker characters. It was intended for experimenting with text transformations that survive simple line-oriented handling.

The implementation preserves newline characters, streams input line by line, and exposes a built-in `test` action for the insert/remove cycle.

## Usage

Commands below run from the repository root. Create an input text file, then
run the self-check without writing output:

```shell
python projects/scripts/altchar/altchar.py test input.txt --char A
```

The self-check now handles multi-line input: insertion skips newline characters and removal skips marker characters only after ordinary characters. Removal also checks that the expected marker is actually present instead of blindly discarding bytes.

Create an ignored artifact directory, then insert and remove the marker using
distinct explicit output paths:

```shell
python -c "from pathlib import Path; Path('artifacts/altchar').mkdir(parents=True, exist_ok=True)"
python projects/scripts/altchar/altchar.py insert input.txt --char A --output artifacts/altchar/inserted.txt
python projects/scripts/altchar/altchar.py remove artifacts/altchar/inserted.txt --char A --output artifacts/altchar/restored.txt
```

Both explicit and default output paths overwrite existing files when they are
distinct from the input. The command rejects an output that refers to the
input file, including resolved path, symbolic-link, and hard-link aliases,
before opening it for writing. Without `--output`, insertion uses the input
name plus `.a` and removal uses the input name plus `.rem`.

Run the co-located tests from the repository root:

```shell
python -m pytest projects/scripts/altchar/tests
```

The transform is reversible only when the same marker string is used and the original text does not contain ambiguous marker sequences. It is text-only and is not compression, encryption, or a general binary-safe encoding.
