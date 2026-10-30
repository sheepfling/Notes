"""Creation must not discard input or replace output after capture errors."""

import builtins
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).resolve().parents[2] / "projects/scripts/textball") / "textball.py"


def run_textball(tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
####


def load_textball():
    from notes_tools.articles import textball
    return textball
####


@pytest.mark.parametrize("mode", ["plain", "encoded", "obfuscated"])
@pytest.mark.parametrize("alias", ["inside", "symlink", "hardlink"])
def test_create_rejects_actual_output_alias_without_replacing_input(
    tmp_path: Path, mode: str, alias: str
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    member = source / "member.txt"
    member.write_bytes(b"source contents")
    suffix = "" if mode == "plain" else ".b64" if mode == "encoded" else ".b64.obs"
    placeholder = source / "package" if alias == "inside" else tmp_path / "package"
    actual = Path(str(placeholder) + suffix)
    if alias == "inside":
        placeholder.write_bytes(b"placeholder contents")
        if actual != placeholder:
            actual.write_bytes(b"existing output")
        ####
    else:
        if actual != placeholder:
            placeholder.write_bytes(b"placeholder contents")
        ####
        try:
            if alias == "symlink":
                actual.symlink_to(member)
            else:
                os.link(member, actual)
            ####
        except OSError as error:
            pytest.skip(f"{alias} unavailable: {error}")
        ####
    ####
    before_placeholder = placeholder.read_bytes()
    before_actual = actual.read_bytes()
    arguments = ["create", str(source), str(placeholder)]
    if mode != "plain":
        arguments.append("--encode")
    ####
    if mode == "obfuscated":
        arguments.extend(["--obfuscate", "5"])
    ####

    result = run_textball(tmp_path, *arguments)

    assert result.returncode != 0
    assert "Output must be outside" in result.stderr or "Output aliases an input file" in result.stderr
    assert member.read_bytes() == b"source contents"
    assert placeholder.read_bytes() == before_placeholder
    assert actual.read_bytes() == before_actual
####


@pytest.mark.parametrize("kind", ["outside-file", "dangling-file", "directory"])
def test_create_rejects_unsafe_or_unreadable_symlinks(
    tmp_path: Path, kind: str
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "secret.txt"
    target.write_bytes(b"outside contents")
    link = source / "link"
    try:
        if kind == "directory":
            link.symlink_to(outside, target_is_directory=True)
        elif kind == "dangling-file":
            link.symlink_to(source / "missing.txt")
        else:
            link.symlink_to(target)
        ####
    except OSError as error:
        pytest.skip(f"symlink unavailable: {error}")
    ####
    output = tmp_path / "output.txt"
    output.write_bytes(b"existing output")

    result = run_textball(tmp_path, "create", str(source), str(output))

    assert result.returncode != 0
    assert output.read_bytes() == b"existing output"
    assert target.read_bytes() == b"outside contents"
####


def test_create_preserves_contained_file_symlink_behavior(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    target = source / "member.txt"
    target.write_bytes(b"inside")
    link = source / "link.txt"
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink unavailable: {error}")
    ####
    package = tmp_path / "package.txt"
    package.touch()
    output = tmp_path / "output"

    created = run_textball(tmp_path, "create", str(source), str(package))
    extracted = run_textball(tmp_path, "extract", str(package), str(output))

    assert created.returncode == 0, created.stderr
    assert extracted.returncode == 0, extracted.stderr
    assert (output / "source" / "member.txt").read_bytes() == b"inside"
    assert (output / "source" / "link.txt").read_bytes() == b"inside"
####


@pytest.mark.parametrize("failure", ["member-read", "walk"])
def test_capture_failure_preserves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    module = load_textball()
    source = tmp_path / "source"
    source.mkdir()
    member = source / "member.txt"
    member.write_bytes(b"source contents")
    output = tmp_path / "package.txt"
    output.write_bytes(b"existing output")
    if failure == "member-read":
        original_open = builtins.open

        def failing_open(path, *args, **kwargs):
            if Path(path) == member:
                raise PermissionError("synthetic read failure")
            ####
            return original_open(path, *args, **kwargs)
        ####

        monkeypatch.setattr(builtins, "open", failing_open)
    else:
        def failing_walk(_directory, *, onerror, followlinks):
            assert not followlinks
            onerror(PermissionError("synthetic walk failure"))
            return iter(())
        ####

        monkeypatch.setattr(module.os, "walk", failing_walk)
    ####
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "create", str(source), str(output)])

    with pytest.raises(PermissionError, match="synthetic"):
        module.main()
    ####
    assert output.read_bytes() == b"existing output"
    assert member.read_bytes() == b"source contents"
####
