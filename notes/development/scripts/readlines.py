"""Print a text file with zero-based line numbers and Python representations."""

from __future__ import annotations

import argparse
from pathlib import Path


def represented_lines(path: Path) -> list[str]:
    """Return numbered ``repr`` strings, retaining newline characters visibly."""

    with path.open("r", encoding="utf-8", newline="") as stream:
        return [f"{index}: {line!r}" for index, line in enumerate(stream)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"input file does not exist: {args.input}")
    print("\n".join(represented_lines(args.input)))


if __name__ == "__main__":
    main()
