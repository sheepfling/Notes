# Base64 file conversion

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

[base64_cli.py](base64_cli.py) is a small standard-library command-line wrapper for converting arbitrary file bytes to Base64 text and back. It reads the complete file into memory, which keeps the implementation simple but makes it unsuitable for very large files.

## Usage

From the repository root, create an ignored artifact directory and encode a file:

```shell
python -c "from pathlib import Path; Path('artifacts/base64').mkdir(parents=True, exist_ok=True)"
python projects/scripts/base64/base64_cli.py encode input.bin artifacts/base64/output.b64
```

Decode it again:

```shell
python projects/scripts/base64/base64_cli.py decode artifacts/base64/output.b64 artifacts/base64/restored.bin
```

The right validation is a byte-for-byte comparison of `input.bin` and the restored
file, not visual inspection of the encoded text. The tool rejects input/output
aliases, including existing symbolic and hard links, but overwrites a distinct
existing destination. Decoding accepts whitespace-wrapped Base64 and rejects
other invalid data before opening the destination.

The runner uses the Python standard library. Run its focused tests from the
repository root with pytest:

```shell
python -m pytest tests/scripts/test_base64_article.py
```

Tests use temporary paths for their generated files and preserve the source.

## Boundaries

Base64 is an encoding, not encryption. Anyone with the text can decode it. It increases size by roughly one third, and this version does not provide authentication or a checksum. For large files, a streaming implementation is preferable; for sensitive data, use authenticated encryption instead.
