"""Round-trip and artifact-location checks for the Altchar note."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "altchar.py"


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
