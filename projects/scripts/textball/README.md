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
output in its own package. Creation rejects a final output inside the input
tree or hard-linked to an input file, including the derived `.b64` and `.obs`
output paths. File symlinks resolving within the input tree retain their previous
content-following behavior; links outside it, dangling links, and directory
symlinks cause an error rather than silently omitting or importing content.
An unreadable or disappearing input also stops creation before the output is
opened. Concurrent changes to paths during capture are not protected.

The encoded form can optionally insert harmless non-Base64 characters:

```shell
python projects/scripts/textball/textball.py create input-directory artifacts/textball/package.txt --encode --obfuscate 5
```

The obfuscated output is written as `package.txt.b64.obs`; pass that path to
the extractor with `--decode` when using this option.

## Text encoding across environments

For portable readable text, specify the same codec when creating and extracting.
For example, use `--text --encoding utf-8` with `create`, then
`--encoding utf-8` with `extract`. Text that cannot be decoded and re-encoded
byte-for-byte with the chosen codec is retained as Base64 bytes. The outer
`--encode`/`--decode` layer continues to use UTF-8 for the inner text stream.

Without `--encoding`, both commands retain their historical locale-dependent
behavior. The v1 format does not record the codec: for an existing archive,
specify the codec used to create it rather than guessing. A wrong codec can
alter non-ASCII path names even when member checksums match. The operating
system's filesystem encoding must also support the stored path names; on
Python, UTF-8 mode may be needed for non-ASCII names in an ASCII locale.

Extract the encoded package into a new directory:

```shell
python projects/scripts/textball/textball.py extract artifacts/textball/package.txt.b64 artifacts/textball/extracted --decode
```

Each member's size and checksum are checked before its destination is opened;
invalid members stop extraction without replacing their destination. Valid
members may still overwrite existing files, but a member cannot overwrite the
input textball itself, even through a symbolic or hard link. Extraction is not transactional:
members written before a later error remain in place. Use a new, empty
destination and retain the original inputs. Creation still overwrites an existing
distinct output package; an output write failure can leave that file incomplete.

Text members preserve their original line endings through the CLI. For older
archives whose Windows output translated line endings, extraction accepts a
restored form only when its recorded size and checksum both match.

Run the Python article tests from the repository root:

```shell
python -m pytest tests/scripts/test_textball_article.py tests/scripts/test_textball_creation_safety.py
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
