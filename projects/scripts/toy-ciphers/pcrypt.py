"""A repeating printable-ASCII passphrase transformation experiment.

This is a toy cipher for studying reversible transformations.  It is not
encryption: it provides no authentication, modern key derivation, nonce,
semantic security, or safe binary-file handling.
"""

from __future__ import annotations

import argparse
from itertools import cycle
from pathlib import Path

PRINTABLE_MIN = 32
PRINTABLE_MAX = 126
PRINTABLE_RANGE = PRINTABLE_MAX - PRINTABLE_MIN + 1


def _is_ascii_printable(character: str) -> bool:
    return len(character) == 1 and PRINTABLE_MIN <= ord(character) <= PRINTABLE_MAX
####


def _shift_character(character: str, key_character: str, direction: int) -> str:
    if not _is_ascii_printable(character):
        return character
    ####
    if not _is_ascii_printable(key_character):
        raise ValueError("passphrases must contain printable ASCII characters")
    ####
    value = (ord(character) - PRINTABLE_MIN + direction * (ord(key_character) - PRINTABLE_MIN))
    return chr(value % PRINTABLE_RANGE + PRINTABLE_MIN)
####


def _require_passphrase(passphrase: str) -> None:
    if not passphrase:
        raise ValueError("passphrase cannot be empty")
    ####
    if any(not _is_ascii_printable(character) for character in passphrase):
        raise ValueError("passphrases must contain printable ASCII characters")
    ####
####


def add_passphrase(source: str, passphrase: str) -> str:
    """Apply a repeating passphrase to *source* without truncating it."""

    _require_passphrase(passphrase)
    return "".join(
        _shift_character(character, key_character, 1)
        for character, key_character in zip(source, cycle(passphrase))
    )
####


def sub_passphrase(source: str, passphrase: str) -> str:
    """Reverse :func:`add_passphrase`."""

    _require_passphrase(passphrase)
    return "".join(
        _shift_character(character, key_character, -1)
        for character, key_character in zip(source, cycle(passphrase))
    )
####


def _same_file(first: Path, second: Path) -> bool:
    """Detect path and existing hard-link aliases before writing output."""
    if first.resolve() == second.resolve():
        return True
    ####
    try:
        return first.samefile(second)
    except FileNotFoundError:
        return False
    ####
####


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    encrypt = subparsers.add_parser("encrypt", help="transform a UTF-8 text file")
    encrypt.add_argument("input", type=Path)
    encrypt.add_argument("passphrase")
    encrypt.add_argument("output", type=Path)

    decrypt = subparsers.add_parser("decrypt", help="reverse a transformed UTF-8 text file")
    decrypt.add_argument("input", type=Path)
    decrypt.add_argument("passphrase")
    decrypt.add_argument("output", type=Path)

    subparsers.add_parser("test", help="run the round-trip self-test")
    args = parser.parse_args()

    if args.action == "test":
        sample = "printable text\nwith Unicode: café\n"
        passphrase = "example"
        assert sub_passphrase(add_passphrase(sample, passphrase), passphrase) == sample
        print("Test was successful")
        return
    ####

    if not args.input.is_file():
        parser.error(f"input file does not exist: {args.input}")
    ####
    if _same_file(args.input, args.output):
        parser.error("input and output must refer to different files")
    ####

    with args.input.open("r", encoding="utf-8", newline="") as stream:
        data = stream.read()
    ####
    if args.action == "encrypt":
        result = add_passphrase(data, args.passphrase)
    else:
        result = sub_passphrase(data, args.passphrase)
    ####
    args.output.write_text(result, encoding="utf-8", newline="")
####


if __name__ == "__main__":
    main()
####
