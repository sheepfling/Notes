# Windows batch-only transfer tools

> Type: collection note  
> Status: needs-review  
> Updated: 2026-08-01

These scripts preserve a practical fallback from the older notes: sometimes the only available
tooling on a Windows machine is `cmd.exe`, `tar.exe`, `certutil.exe`, and a few batch files. They
are useful for moving or checking large payloads in that constrained environment.

The safer scripts do not delete their inputs and refuse to overwrite an existing output. They are
still thin wrappers around command-line tools, so inspect the paths and archive contents before
running them.

## Tar packing and unpacking

`tar.exe` is required. Pack a directory into an ordinary tar archive:

```bat
pack-tar.bat <input-directory> <output.tar>
```

List an archive before extraction, then extract it into a new directory:

```bat
verify-tar.bat <input.tar>
unpack-tar.bat <input.tar> <new-output-directory>
```

The verification step confirms that `tar` can read the archive and prints its entries. It is not
a cryptographic signature or a complete content-integrity proof. For a stronger transfer record,
also save the SHA-256 digest:

```bat
hash-sha256.bat <input.tar>
```

The wrappers intentionally refuse to extract into an existing directory, which makes accidental
merges less likely. Review archives from untrusted sources before extraction.

## Base64 fallback

`certutil.exe` can encode and decode files when a Python runtime is unavailable:

```bat
b64-encode-recursive.bat <directory>
b64-decode-recursive.bat <directory>
b64-decode.bat <encoded-file> <decoded-file>
```

The recursive tools append or remove `.b64.txt`, retain both source and output files, skip an
existing output, and return a failure code if any conversion fails. Base64 is an interchange
encoding, not compression, encryption, authentication, or a way to reduce a large file.

## Historical text transforms

The old `altchar.bat` and `untextball.bat` workflows are retained as compatibility references.
They operate on line-oriented text and are not general binary tools. In particular, `cmd.exe`
line expansion has practical length limits, `echo` cannot faithfully represent every whitespace
line, and the textball format must be treated as trusted input. Prefer the Python implementations
when they are available, and compare a pre/post-transfer hash for important files.

The unfinished `sub_A.bat` experiment is intentionally not promoted as a runnable tool.
