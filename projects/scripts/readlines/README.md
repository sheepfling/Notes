# Line representation helper

> Type: project note
> Status: diagnostic helper
> Updated: 2026-08-02

[`readlines.py`](readlines.py) displays each line with its index and escaped line ending. It is
useful when diagnosing files that differ only in newline style or final-newline handling.

It does not modify the input file and is intentionally kept separate from the transfer and
encoding experiments.
