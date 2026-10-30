# Debugging Python and native crash dumps

> Type: troubleshooting  
> Status: needs-review  
> Updated: 2026-08-01

An error such as “not in executable format” means the debugger was given a file that is not a
readable core dump for that debugger. A path mounted from Windows does not prove that the file is
invalid, and WSL does not by itself explain every failed core-dump investigation. Identify the
file and the exact executable first.

## Identify the dump

Run the `file` command inside the Linux environment that produced the dump:

```bash
file <core-file>
```

A usable Linux dump normally identifies itself as an ELF core file and includes the architecture.
ASCII text, a truncated file, an ordinary log, or a Windows-format dump needs a different
diagnostic path. Keep the dump in a Linux-native location while investigating when possible, and
make sure there is enough free space for it.

## Open it with the matching executable

Use the same Python executable or native program that created the dump, ideally with debug symbols:

```bash
gdb <matching-executable> <core-file>
```

Then start with:

```gdb
bt
info threads
thread apply all bt
info registers
```

If GDB reports no stack or registers, common causes include a mismatched executable, missing
symbols, a truncated/incomplete dump, or a crash that did not capture the expected process state.
For Python, native extensions and the interpreter build matter; a Python traceback alone may not
explain a segmentation fault in compiled code.

## Check whether Linux is configured to write cores

On a native Linux or WSL environment, inspect:

```bash
uname -a
ulimit -c
cat /proc/sys/kernel/core_pattern
```

`ulimit -c` must permit a non-zero dump, commonly `unlimited` during a controlled debugging
session. If `core_pattern` starts with a pipe, another crash handler may be receiving the dump
instead of writing a file in the current directory. Follow that handler's storage and retention
rules rather than assuming the missing file is corrupt.

## Prefer Python-level diagnostics when appropriate

For an ordinary Python exception, use the traceback. For interpreter or extension crashes, enable
the standard-library fault handler:

```bash
export PYTHONFAULTHANDLER=1
python -X faulthandler -m pytest
```

Or enable it in a minimal reproducer:

```python
import faulthandler

faulthandler.enable()
```

Build native extensions with symbols and without stripping them when a native backtrace is needed.
Record the Python version, executable path, extension versions, operating environment, and the
exact command that produced the dump; those details determine whether a backtrace is meaningful.
