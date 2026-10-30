"""A printable-ASCII one-time-pad-shaped transformation experiment.

This is a text transformation exercise, not a secure encryption tool.  The key
must be kept secret and at least as long as the input, but the format is not a
modern authenticated encryption format and should not protect real data.
"""

from __future__ import annotations

import argparse
import secrets
from pathlib import Path

PRINTABLE_MIN = 32
PRINTABLE_MAX = 126
PRINTABLE_ALPHABET = "".join(chr(value) for value in range(PRINTABLE_MIN, PRINTABLE_MAX + 1))
PRINTABLE_RANGE = len(PRINTABLE_ALPHABET)


def is_ascii_printable(character: str) -> bool:
    """Return whether *character* is in the transform's printable alphabet."""

    return len(character) == 1 and PRINTABLE_MIN <= ord(character) <= PRINTABLE_MAX
####


def make_otp(length: int) -> str:
    """Create a printable key of exactly *length* characters."""

    if length < 0:
        raise ValueError("key length cannot be negative")
    ####
    return "".join(secrets.choice(PRINTABLE_ALPHABET) for _ in range(length))
####


def _shift_character(character: str, key_character: str, direction: int) -> str:
    if not is_ascii_printable(character):
        return character
    ####
    if not is_ascii_printable(key_character):
        raise ValueError("keys must contain printable ASCII characters")
    ####
    value = (ord(character) - PRINTABLE_MIN + direction * (ord(key_character) - PRINTABLE_MIN))
    return chr(value % PRINTABLE_RANGE + PRINTABLE_MIN)
####


def _require_equal_lengths(source: str, key: str) -> None:
    if len(source) != len(key):
        raise ValueError(f"source and key lengths differ: {len(source)} != {len(key)}")
    ####
####


def add_otp(source: str, key: str) -> str:
    """Transform printable characters with a same-length key."""

    _require_equal_lengths(source, key)
    return "".join(_shift_character(character, key_character, 1) for character, key_character in zip(source, key))
####


def sub_otp(source: str, key: str) -> str:
    """Reverse :func:`add_otp` with the same key."""

    _require_equal_lengths(source, key)
    return "".join(_shift_character(character, key_character, -1) for character, key_character in zip(source, key))
####


def _read(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()
    ####
####


def _write(path: Path, data: str) -> None:
    path.write_text(data, encoding="utf-8", newline="")
####


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    encrypt = subparsers.add_parser("encrypt", help="transform a UTF-8 text file")
    encrypt.add_argument("input", type=Path)
    encrypt.add_argument("output", type=Path)
    encrypt.add_argument("key_output", type=Path)

    decrypt = subparsers.add_parser("decrypt", help="reverse a transformed UTF-8 text file")
    decrypt.add_argument("input", type=Path)
    decrypt.add_argument("key", type=Path)
    decrypt.add_argument("output", type=Path)

    subparsers.add_parser("test", help="run the round-trip self-test")
    args = parser.parse_args()

    if args.action == "test":
        sample = "printable text\nwith Unicode: café\n"
        key = make_otp(len(sample))
        assert sub_otp(add_otp(sample, key), key) == sample
        print("Test was successful")
        return
    ####

    if not args.input.is_file():
        parser.error(f"input file does not exist: {args.input}")
    ####

    if args.action == "encrypt":
        data = _read(args.input)
        key = make_otp(len(data))
        _write(args.output, add_otp(data, key))
        _write(args.key_output, key)
    else:
        if not args.key.is_file():
            parser.error(f"key file does not exist: {args.key}")
        ####
        _write(args.output, sub_otp(_read(args.input), _read(args.key)))
    ####
####


if __name__ == "__main__":
    main()
####
