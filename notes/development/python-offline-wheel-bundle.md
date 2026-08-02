# Build an offline Python wheel bundle

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

When a Python environment must be installed without network access, prepare a directory of
wheel files on a connected machine. Keep the bundle outside this Notes repository: wheels are
generated artifacts and may be platform-specific or contain native binaries.

## Create the bundle

Start from a clean environment that matches the target Python version, operating system, CPU
architecture, and dependency set. Export the exact requirements, then ask pip to download the
required distributions into a separate directory:

```bash
python -m pip freeze > requirements.txt
mkdir -p wheels
python -m pip download \
  --requirement requirements.txt \
  --only-binary=:all: \
  --dest wheels
```

`pip download` resolves and downloads distributions without installing them. The
`--only-binary=:all:` option intentionally fails when a requirement has no compatible binary
distribution; either build that package separately or decide explicitly that source builds are
acceptable. See the [pip download documentation](https://pip.pypa.io/en/stable/cli/pip_download/)
for platform and Python-version selection options.

Do not export from an environment that contains unrelated development packages. For a
reproducible bundle, write a small requirements file containing only the application’s direct
requirements, pin versions, and run the download for each target platform if more than one is
needed.

## Verify and transfer

Record the contents and checksums outside the application source tree:

```bash
find wheels -maxdepth 1 -type f -print | sort
sha256sum wheels/* > wheels.sha256
sha256sum --check wheels.sha256
```

On Windows, use `Get-FileHash` or the platform’s checksum utility instead of `sha256sum`.
Transfer `requirements.txt`, the `wheels/` directory, and its checksum manifest through the
approved offline-transfer process. Do not commit the wheel files or the manifest when it reveals
private package names or internal indexes.

## Install without an index

On the offline machine, validate the checksums and install only from the bundle:

```bash
python -m pip install \
  --no-index \
  --find-links wheels \
  --requirement requirements.txt
```

`--no-index` prevents pip from silently falling back to a network package index. If installation
fails, check that every dependency has a compatible wheel and that the bundle was made for the
same Python ABI and platform. A wheel downloaded for one operating system or architecture may
not work on another.

## Failure modes

- A missing transitive dependency usually means the requirements file was incomplete or the
  download was restricted to a platform different from the target.
- A package with no wheel under `--only-binary=:all:` needs a deliberate source-build plan or a
  different package/version; do not quietly mix an unreviewed compiler toolchain into an offline
  install.
- Native-extension import errors often indicate a Python-version, ABI, operating-system, or CPU
  mismatch rather than a pip resolver problem.
- A bundle built from a mutable environment is difficult to audit. Prefer a disposable virtual
  environment and retain the exact requirements file used to produce it.
