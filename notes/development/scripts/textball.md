# Packing a directory into a text-only stream

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## The idea

[`textball.py`](textball.py) is a small experiment in making a directory portable through text-only channels. It writes a line-oriented tar-like stream containing each path, line count, newline information, byte size, and MD5 checksum. Binary files are Base64-encoded; text can optionally remain readable.

This is useful when the transport accepts text but not an ordinary archive. It is not a replacement for a normal tar, ZIP, or authenticated backup.

## Create and extract

Create a text package:

```powershell
New-Item package.txt -ItemType File
python textball.py create input-directory package.txt --encode
```

The current implementation expects the output path to already exist before it creates the package; that is a small usability bug worth fixing in a future revision.

The encoded form can optionally insert harmless non-Base64 characters:

```powershell
python textball.py create input-directory package.txt --encode --obfuscate 5
```

Extract it into a new directory:

```powershell
python textball.py extract package.txt extracted-directory --decode
```

The checksums and sizes are checked after extraction, so corruption should be visible.

## Caveats before trusting it

- The format is custom and has no versioned schema or cryptographic authentication.
- MD5 detects accidental corruption but does not protect against intentional tampering.
- The extractor joins a stored path directly to the output directory. Do not extract untrusted textballs until path traversal and absolute-path handling have been hardened.
- The implementation reads file contents into memory and is intended for small or moderate collections.
- The text stream is not encryption; Base64 and inserted characters provide encoding or obfuscation only.
