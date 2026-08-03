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

## Recommended transfer bundle

When the receiving side has only the Windows command prompt, built-in `tar.exe`, and
`certutil.exe`, pack the directory once and transfer the generated `.b64.txt` file together with
its `.sha256` sidecar:

```bat
pack-transfer.bat <input-directory> <output-prefix>
unpack-transfer.bat <output-prefix>.tar.gz.b64.txt <new-output-directory>
```

For example, an output prefix of `payload` creates:

- `payload.tar.gz` — compressed archive retained for local recovery;
- `payload.tar.gz.b64.txt` — text-safe transfer artifact;
- `payload.tar.gz.sha256` — digest checked automatically during unpacking.
- `payload.tar.gz.manifest.txt` — `NOTES-TRANSFER/1` format and encoding declaration.

The output prefix should be outside the input directory. The receiving directory must not already
exist. New bundles require the manifest before unpacking; historical bundles can be handled with
`unpack-transfer.bat <encoded-file> <output-directory> --legacy`. The archive should still be
treated as trusted input; the hash verifies transfer integrity, not sender identity or archive safety.

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

## Related fallback projects

The `certutil.exe` Base64 scripts now live in the [Base64 project](../base64/README.md). The
legacy text-only extractor lives in the [textball project](../textball/README.md), and the marker
transform lives in the [altchar project](../altchar/README.md). Each README explains the relevant
limitations and preferred Python implementation.

The unfinished `sub_A.bat` experiment is intentionally not promoted as a runnable tool.
