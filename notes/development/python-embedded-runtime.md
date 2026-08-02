# Python’s Windows embeddable distribution

> Type: reference  
> Status: historical  
> Updated: 2026-08-01

The Windows embeddable Python package is intentionally minimal. It is useful when an application
ships a private interpreter, but it is not equivalent to a normal Python installation or a virtual
environment. A full Python installation with a virtual environment is usually easier to maintain.

## Why ordinary package installation fails

An embeddable distribution may contain a versioned `pythonXY._pth` file and omit normal site
initialization. In that mode, Python does not automatically search `site-packages`, and `pip` is
not included by default.

If the embedding application permits it, enable site initialization in the matching `_pth` file
by uncommenting:

```text
import site
```

Make the smallest possible change and keep a copy of the original file. The application may rely
on the isolation that the `_pth` file provides.

## Add packaging support carefully

Use a disposable copy of the embedded runtime. Obtain a compatible `get-pip.py` from the official
packaging source, verify the download, and run it with the embedded interpreter:

```powershell
& .\python.exe .\get-pip.py
& .\python.exe -m pip --version
```

Do not commit `get-pip.py`, installed packages, or the embedded runtime to this Notes repository.
Install only the packages required by the host application:

```powershell
& .\python.exe -m pip install <package-name>
```

For repeatable setup, capture a reviewed requirements file and use the [Python Windows embedding
documentation](https://docs.python.org/3/using/windows.html#embedded-distribution) for the exact
runtime version and application constraints.

## Troubleshooting

- Confirm that the `_pth` filename matches the interpreter version.
- Run `python.exe -m pip`, not a possibly unrelated `pip.exe` found on `PATH`.
- Check `python.exe -c "import sys; print(sys.path)"` to see where modules are searched.
- Keep separate embedded runtimes for incompatible Python ABIs.
- If the host application expects isolation, prefer its documented package mechanism over adding
  global `site` initialization.

This note is a memory aid for an old embedded-runtime setup, not a recommendation to modify a
managed application’s private Python installation without testing.
