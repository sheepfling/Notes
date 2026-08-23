#!/usr/bin/env python3
"""Validate Markdown links in the Notes repository."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(\s*<?([^)>\s]+)", re.MULTILINE)
REFERENCE_LINK = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
SKIP_PARTS = {".git", ".uv-cache", ".pytest_cache", "artifacts", "build", "inbox"}


@dataclass(frozen=True)
class Link:
    source: Path
    target: str
####


def markdown_files(repo_root: Path) -> list[Path]:
    return [
        path
        for path in repo_root.rglob("*.md")
        if not any(
            part in SKIP_PARTS or part.startswith(".venv")
            for part in path.relative_to(repo_root).parts
        )
    ]
####


def links_in(path: Path) -> list[Link]:
    text = path.read_text(encoding="utf-8")
    targets = MARKDOWN_LINK.findall(text) + REFERENCE_LINK.findall(text)
    return [Link(path, target.strip("<>").strip()) for target in targets]
####


def heading_slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"\s+", "-", value)
####


def headings(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {heading_slug(match) for match in HEADING.findall(text)}
####


def is_ignored(repo_root: Path, target: Path) -> bool:
    relative = target.relative_to(repo_root)
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", "--", str(relative)],
        cwd=repo_root,
        check=False,
    )
    return result.returncode == 0
####


def validate_local_link(repo_root: Path, link: Link) -> str | None:
    raw_target = unquote(link.target)
    split = urlsplit(raw_target)
    if split.scheme or raw_target.startswith(("/", "\\", "//")):
        return None
    ####

    relative_target = split.path
    target = (link.source.parent / relative_target).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError:
        return f"link resolves outside repository: {link.target}"
    ####

    if not target.exists():
        return f"missing local target: {link.target}"
    ####
    if is_ignored(repo_root, target):
        return f"link resolves to an ignored path: {link.target}"
    ####

    if split.fragment and split.fragment not in headings(target if target.is_file() else link.source):
        return f"missing heading anchor: {link.target}"
    ####
    return None
####


def external_links(links: list[Link]) -> list[Link]:
    return [
        link
        for link in links
        if urlsplit(link.target).scheme in {"http", "https"}
    ]
####


def check_external(link: Link, timeout: float) -> str | None:
    request = Request(
        link.target,
        headers={"User-Agent": "notes-link-validator/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status in {404, 410}:
                return f"HTTP {response.status}: {link.target}"
            ####
        ####
    except HTTPError as error:
        if error.code in {404, 410}:
            return f"HTTP {error.code}: {link.target}"
        ####
        if error.code >= 500:
            return f"HTTP {error.code}: {link.target}"
        ####
    except URLError as error:
        return f"external link could not be checked ({error.reason}): {link.target}"
    except OSError as error:
        return f"external link could not be checked ({error}): {link.target}"
    except ValueError as error:
        return f"external link could not be checked ({error}): {link.target}"
    ####
    return None
####


def validate(repo_root: Path, *, check_web: bool, timeout: float) -> list[str]:
    errors: list[str] = []
    all_links: list[Link] = []
    for path in markdown_files(repo_root):
        links = links_in(path)
        all_links.extend(links)
        for link in links:
            target = urlsplit(link.target)
            if target.scheme in {"http", "https", "mailto"}:
                continue
            ####
            if target.scheme or link.target.startswith(("/", "\\", "//")):
                errors.append(f"{link.source}: absolute or unsupported link: {link.target}")
                continue
            ####
            error = validate_local_link(repo_root, link)
            if error:
                errors.append(f"{link.source}: {error}")
            ####
        ####
    ####

    if check_web:
        seen: set[str] = set()
        for link in external_links(all_links):
            if link.target in seen:
                continue
            ####
            seen.add(link.target)
            error = check_external(link, timeout)
            if error:
                errors.append(f"{link.source}: {error}")
            ####
        ####
    ####
    return errors
####


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", action="store_true", help="Check HTTP(S) links.")
    parser.add_argument("--timeout", type=float, default=10.0)
    arguments = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    errors = validate(repo_root, check_web=arguments.external, timeout=arguments.timeout)
    if errors:
        print("Notes validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    ####
    mode = "local and external links" if arguments.external else "local links"
    print(f"Notes validation passed for {mode}.")
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
