# Base64 file conversion

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

[base64_cli.py](base64_cli.py) is a small standard-library command-line wrapper for converting arbitrary file bytes to Base64 text and back. It reads the complete file into memory, which keeps the implementation simple but makes it unsuitable for very large files.

## Usage

Encode a file:

```
python base64_cli.py encode input.bin output.b64
```

Decode it again:

```
python base64_cli.py decode output.b64 restored.bin
```

The right validation is a byte-for-byte comparison of `input.bin` and `restored.bin`, not visual inspection of the encoded text.

## Boundaries

Base64 is an encoding, not encryption. Anyone with the text can decode it. It increases size by roughly one third, and this version does not provide authentication or a checksum. For large files, a streaming implementation is preferable; for sensitive data, use authenticated encryption instead.
