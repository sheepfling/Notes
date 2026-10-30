"""Tests for line-ending representation."""

import importlib.util
from pathlib import Path


def test_readlines_represents_line_endings(tmp_path: Path) -> None:
    script = (Path(__file__).resolve().parents[2] / "projects/scripts/readlines") / "readlines.py"
    spec = importlib.util.spec_from_file_location("readlines", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "lines.txt"
    source.write_text("one\nlast", encoding="utf-8", newline="")

    assert module.represented_lines(source) == ["0: 'one\\n'", "1: 'last'"]
    assert source.read_text(encoding="utf-8") == "one\nlast"
    assert {path.name for path in tmp_path.iterdir()} == {"lines.txt"}
####
