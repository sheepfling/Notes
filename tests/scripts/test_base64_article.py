"""Exercise the Base64 article's existing CLI with temporary files."""

import base64
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).resolve().parents[2] / "projects/scripts/base64") / "base64_cli.py"


def test_base64_cli_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    encoded = tmp_path / "source.b64"
    restored = tmp_path / "restored.bin"
    original = bytes(range(256))
    source.write_bytes(original)

    for action, input_path, output_path in (
        ("encode", source, encoded),
        ("decode", encoded, restored),
    ):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), action, str(input_path), str(output_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    ####

    assert source.read_bytes() == original
    assert encoded.read_bytes() == base64.b64encode(original)
    assert restored.read_bytes() == original
    assert {path.name for path in tmp_path.iterdir()} == {"source.bin", "source.b64", "restored.bin"}
####


@pytest.mark.parametrize("action", ["encode", "decode"])
@pytest.mark.parametrize("alias", ["same", "relative", "symlink", "hardlink"])
def test_base64_rejects_input_output_alias(tmp_path: Path, action: str, alias: str) -> None:
    source = tmp_path / "source.bin"
    original = b"YWJj" if action == "decode" else b"abc"
    source.write_bytes(original)
    output = source if alias == "same" else tmp_path / "alias.bin"
    if alias == "relative":
        output = Path("source.bin")
    elif alias == "symlink":
        try:
            output.symlink_to(source)
        except OSError as error:
            pytest.skip(f"symlinks unavailable: {error}")
        ####
    elif alias == "hardlink":
        try:
            os.link(source, output)
        except OSError as error:
            pytest.skip(f"hard links unavailable: {error}")
        ####
    ####
    result = subprocess.run(
        [sys.executable, str(SCRIPT), action, str(source), str(output)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "different files" in result.stderr
    assert source.read_bytes() == original
####


def test_base64_rejects_invalid_data_without_overwriting_output(tmp_path: Path) -> None:
    source = tmp_path / "bad.b64"
    destination = tmp_path / "output.bin"
    source.write_bytes(b"@@@@")
    destination.write_bytes(b"preserve")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "decode", str(source), str(destination)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert destination.read_bytes() == b"preserve"
####


def test_base64_decodes_wrapped_data_and_overwrites_distinct_output(tmp_path: Path) -> None:
    source = tmp_path / "wrapped.b64"
    destination = tmp_path / "output.bin"
    source.write_bytes(b"Y W\nJj\r\n")
    destination.write_bytes(b"old")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "decode", str(source), str(destination)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert destination.read_bytes() == b"abc"
####


def test_base64_encode_still_overwrites_distinct_output(tmp_path: Path) -> None:
    source = tmp_path / "input.bin"
    destination = tmp_path / "output.b64"
    source.write_bytes(b"abc")
    destination.write_bytes(b"old")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "encode", str(source), str(destination)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert source.read_bytes() == b"abc"
    assert destination.read_bytes() == b"YWJj"
####
