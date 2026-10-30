# Packing a directory into a text-only stream

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

[`textball.py`](textball.py) is a small experiment in making a directory portable through text-only channels. It writes a line-oriented tar-like stream containing each path, line count, newline information, byte size, and MD5 checksum. Binary files are Base64-encoded; text can optionally remain readable.

Every new stream begins with the `NOTES-TEXTBALL/1` format marker. Extractors reject missing or
unknown markers by default; use `--legacy` only for trusted historical streams created before
the marker was introduced.

This is useful when the transport accepts text but not an ordinary archive. It is not a replacement for a normal tar, ZIP, or authenticated backup.

## Create and extract

From the repository root, create an ignored artifact directory and an empty
package placeholder, then create a text package from an existing input directory:

```shell
python -c "from pathlib import Path; Path('artifacts/textball').mkdir(parents=True, exist_ok=True); Path('artifacts/textball/package.txt').touch()"
python projects/scripts/textball/textball.py create input-directory artifacts/textball/package.txt --encode
```

The current implementation expects the package placeholder to exist before
creation. With `--encode`, it writes `package.txt.b64` beside that placeholder.
Keep the artifact directory outside the input directory to avoid including the
output in its own package.

The encoded form can optionally insert harmless non-Base64 characters:

```shell
python projects/scripts/textball/textball.py create input-directory artifacts/textball/package.txt --encode --obfuscate 5
```

The obfuscated output is written as `package.txt.b64.obs`; pass that path to
the extractor with `--decode` when using this option.

Extract the encoded package into a new directory:

```shell
python projects/scripts/textball/textball.py extract artifacts/textball/package.txt.b64 artifacts/textball/extracted --decode
```

The checksums and sizes are checked after extraction, so corruption should be visible.
Extraction can overwrite existing files before validation, so use a new, empty
destination and retain the original inputs. Creation can also overwrite an
existing output package.

Run the Python article tests from the repository root:

```shell
python -m pytest projects/scripts/textball/tests
```

They use temporary directories for packages and extracted files. The Windows
batch extractor shares the cross-project batch checks in
`tests/test_batch_collection.py` and requires Windows tooling for execution.

## Caveats before trusting it

- The format is custom and has no versioned schema or cryptographic authentication.
- MD5 detects accidental corruption but does not protect against intentional tampering.
- The format has no cryptographic authentication; treat archives from untrusted sources with
  caution even though path traversal is rejected.
- Stored paths are now rejected when they are absolute or contain `..`, and extraction is kept
  inside the requested output directory.
- The implementation reads file contents into memory and is intended for small or moderate collections.
- The text stream is not encryption; Base64 and inserted characters provide encoding or obfuscation only.
