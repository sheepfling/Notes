"""Reject machine-specific paths and private addresses in note content."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXCLUDED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".uv-cache",
    ".venv",
    "build",
    "__pycache__",
    "artifacts",
    "inbox",
}
TEXT_EXTENSIONS = {
    ".bat",
    ".cfg",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
    ".glsl",
}

PRIVATE_IPV4 = re.compile(
    r"(?<![\w.])(?:"
    r"10\.(?:\d{1,3}\.){2}\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}|"
    r"192\.168\.(?:\d{1,3}\.)\d{1,3}"
    r")(?:/\d{1,2})?(?![\w.])"
)

# Placeholder forms are intentionally allowed because they preserve the shape of a reusable
# procedure without identifying a machine: C:\\Users\\<user>, /Users/REPLACE_ME, and so on.
WINDOWS_USER_PATH = re.compile(
    r"(?i)(?:[A-Z]:\\Users\\)(?!<[^>]+>|%USERPROFILE%|your_username|YourUsername|REPLACE_ME)"
    r"[^`\"'\s/\\]+[/\\]"
)
POSIX_USER_PATH = re.compile(
    r"(?i)(?:/(?:mnt/c/)?Users/)(?!<[^>]+>|%USERPROFILE%|your_username|YourUsername|REPLACE_ME)"
    r"[^`\"'\s/\\]+[/\\]"
)
HOME_PATH = re.compile(
    r"(?i)(?:/home/)(?!<[^>]+>|your_user_name|username|REPLACE_ME)[^`\"'\s/\\]+[/\\]"
)


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        ####
        relative_parts = path.relative_to(root).parts
        if any(
            part in EXCLUDED_DIRECTORIES
            or part.startswith(".venv")
            or part in {"venv", "env", "ENV"}
            for part in relative_parts
        ):
            continue
        ####
        yield path
    ####
####


def find_forbidden_matches(text: str, forbidden: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for label, pattern in (
        ("private IPv4 address", PRIVATE_IPV4),
        ("machine-specific Windows user path", WINDOWS_USER_PATH),
        ("machine-specific mounted user path", POSIX_USER_PATH),
        ("machine-specific home path", HOME_PATH),
    ):
        if pattern.search(text):
            findings.append((label, pattern.pattern))
        ####
    ####
    lowered = text.casefold()
    for value in forbidden:
        if value and value.casefold() in lowered:
            findings.append(("caller-supplied private value", value))
        ####
    ####
    return findings
####


def scan(root: Path, forbidden: tuple[str, ...] = ()) -> list[str]:
    results: list[str] = []
    for path in iter_text_files(root):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            findings = find_forbidden_matches(line, forbidden)
            for label, _ in findings:
                results.append(f"{path.relative_to(root)}:{number}: {label}: {line.strip()}")
            ####
        ####
    ####
    return results
####


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--forbidden",
        action="append",
        default=[],
        help="Literal private value to check; pass it at runtime, never commit it to this repository.",
    )
    args = parser.parse_args()
    findings = scan(args.root.resolve(), tuple(args.forbidden))
    if findings:
        print("Scrub validation failed:")
        print("\n".join(f"- {finding}" for finding in findings))
        return 1
    ####
    print("Scrub validation passed for generic private paths and addresses.")
    return 0
####


if __name__ == "__main__":
    sys.exit(main())
####
