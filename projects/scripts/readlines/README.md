# Line representation helper

> Type: project note
> Status: diagnostic helper
> Updated: 2026-08-02

[`readlines.py`](readlines.py) displays each line with its index and escaped line ending. It is
useful when diagnosing files that differ only in newline style or final-newline handling.

It does not modify the input file and is intentionally kept separate from the transfer and
encoding experiments.

From the repository root, inspect a file or run its focused tests:

```shell
python projects/scripts/readlines/readlines.py input.txt
python -m pytest projects/scripts/readlines/tests
```

The helper writes its representation to standard output and creates no output files. The test
uses a temporary input and checks that it remains unchanged.
