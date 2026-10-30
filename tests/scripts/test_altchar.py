"""Round-trip and artifact-location checks for the Altchar note."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).resolve().parents[2] / "projects/scripts/altchar") / "altchar.py"


@pytest.mark.parametrize(
    ("original", "expected_inserted"),
    [("abcd", "aAbAcAdA"), ("ab\ncd\n", "aAbA\ncAdA\n")],
)
def test_round_trip_writes_only_requested_artifacts(
    tmp_path: Path, original: str, expected_inserted: str
) -> None:
    source = tmp_path / "source.txt"
    inserted = tmp_path / "inserted.txt"
    restored = tmp_path / "restored.txt"
    source.write_text(original, encoding="utf-8")

    for action, input_path, output_path in (
        ("insert", source, inserted),
        ("remove", inserted, restored),
    ):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), action, str(input_path), "--char", "A", "--output", str(output_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    ####

    assert source.read_text(encoding="utf-8") == original
    assert inserted.read_text(encoding="utf-8") == expected_inserted
    assert restored.read_text(encoding="utf-8") == original
    assert {path.name for path in tmp_path.iterdir()} == {"source.txt", "inserted.txt", "restored.txt"}
####


def test_default_output_is_next_to_input(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("ab", encoding="utf-8")
    article_entries = {path.name for path in SCRIPT.parent.iterdir()}

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "insert", str(source), "--char", "A"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert source.read_text(encoding="utf-8") == "ab"
    assert (tmp_path / "source.txt.a").read_text(encoding="utf-8") == "aAbA"
    assert {path.name for path in tmp_path.iterdir()} == {"source.txt", "source.txt.a"}
    assert {path.name for path in SCRIPT.parent.iterdir()} == article_entries
####


@pytest.mark.parametrize("action,original", [("insert", "ab"), ("remove", "aAbA")])
@pytest.mark.parametrize("alias_kind", ["same", "relative", "dotdot", "symlink", "hardlink"])
def test_same_file_output_is_rejected(
    tmp_path: Path, action: str, original: str, alias_kind: str
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(original, encoding="utf-8")
    if alias_kind == "same":
        output = source
    elif alias_kind == "relative":
        output = Path("source.txt")
    elif alias_kind == "dotdot":
        (tmp_path / "nested").mkdir()
        output = Path("nested") / ".." / "source.txt"
    elif alias_kind == "symlink":
        output = tmp_path / "alias.txt"
        try:
            output.symlink_to(source)
        except OSError as error:
            pytest.skip(f"symlinks unavailable: {error}")
        ####
    else:
        output = tmp_path / "alias.txt"
        try:
            os.link(source, output)
        except OSError as error:
            pytest.skip(f"hard links unavailable: {error}")
        ####
    ####

    result = subprocess.run(
        [sys.executable, str(SCRIPT), action, str(source), "--char", "A", "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "input and output must refer to different files" in result.stderr
    assert source.read_text(encoding="utf-8") == original
####


def test_default_output_aliasing_input_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("ab", encoding="utf-8")
    try:
        (tmp_path / "source.txt.a").symlink_to(source)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")
    ####

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "insert", str(source), "--char", "A"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "input and output must refer to different files" in result.stderr
    assert source.read_text(encoding="utf-8") == "ab"
####


def test_missing_input_does_not_truncate_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "output.txt"
    output.write_text("preserve", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "insert", str(tmp_path / "missing.txt"), "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert output.read_text(encoding="utf-8") == "preserve"
####


def test_self_check_leaves_input_and_directory_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("ab\ncd\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "test", str(source), "--char", "A"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert source.read_text(encoding="utf-8") == "ab\ncd\n"
    assert {path.name for path in tmp_path.iterdir()} == {"source.txt"}
####


@pytest.mark.parametrize("action,original,expected", [("insert", "ab", "aAbA"), ("remove", "aAbA", "ab")])
@pytest.mark.parametrize("output_kind", ["explicit", "default"])
def test_distinct_existing_output_is_still_overwritten(
    tmp_path: Path, action: str, original: str, expected: str, output_kind: str
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(original, encoding="utf-8")
    output = tmp_path / ("output.txt" if output_kind == "explicit" else f"source.txt.{ 'a' if action == 'insert' else 'rem' }")
    output.write_text("old", encoding="utf-8")
    command = [sys.executable, str(SCRIPT), action, str(source), "--char", "A"]
    if output_kind == "explicit":
        command.extend(["--output", str(output)])
    ####

    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert source.read_text(encoding="utf-8") == original
    assert output.read_text(encoding="utf-8") == expected
####
