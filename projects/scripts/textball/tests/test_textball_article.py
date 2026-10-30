"""Exercise the Textball note's CLI and trusted-input safeguards."""

import base64
import importlib.util
import io
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "textball.py"


def run_textball(tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
####


def load_textball(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
####


def test_textball_round_trip_text_and_binary(tmp_path: Path) -> None:
    source_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    package = tmp_path / "package.txt"
    source_dir.mkdir()
    (source_dir / "hello.txt").write_text("hello\n", encoding="utf-8")
    (source_dir / "bytes.bin").write_bytes(bytes(range(32)))
    package.touch()

    create = run_textball(tmp_path, "create", str(source_dir), str(package), "--encode")
    encoded_package = Path(str(package) + ".b64")
    extract = run_textball(tmp_path, "extract", str(encoded_package), str(output_dir), "--decode")

    assert create.returncode == 0, create.stderr
    assert extract.returncode == 0, extract.stderr
    decoded_text = base64.b64decode(encoded_package.read_text(encoding="utf-8")).decode()
    assert decoded_text.startswith("NOTES-TEXTBALL/1\n")
    assert (output_dir / source_dir.name / "hello.txt").read_text(encoding="utf-8") == "hello\n"
    assert (output_dir / source_dir.name / "bytes.bin").read_bytes() == bytes(range(32))
    assert (source_dir / "hello.txt").read_text(encoding="utf-8") == "hello\n"
    assert {path.name for path in tmp_path.iterdir()} == {"input", "output", "package.txt", "package.txt.b64"}
####


def test_textball_rejects_unknown_format_and_traversal(tmp_path: Path) -> None:
    module = load_textball("textball_safety")
    output_dir = tmp_path / "output"

    with pytest.raises(RuntimeError, match="Unsupported textball format"):
        module.extract_tarball(io.StringIO("not-a-textball\n"), output_dir)
    ####
    assert not output_dir.exists()

    traversal = (
        "NOTES-TEXTBALL/1\n"
        "'../escape.txt'\t1\t0\t1\t"
        "{'path': '../escape.txt', 'num_lines': 1, 'is_base64': False, "
        "'has_trailing_newline': True, 'file_size': 8, 'md5': 'invalid'}\n"
        "contents\n"
    )
    with pytest.raises(RuntimeError, match="Unsafe path"):
        module.extract_tarball(io.StringIO(traversal), output_dir)
    ####
    assert not output_dir.exists()
####


def test_textball_legacy_requires_explicit_opt_in(tmp_path: Path) -> None:
    module = load_textball("textball_legacy")
    legacy = (
        "'legacy.txt'\t1\t0\t1\t"
        "{'path': 'legacy.txt', 'num_lines': 1, 'is_base64': False, "
        "'has_trailing_newline': True, 'file_size': 7, 'md5': 'invalid'}\n"
        "legacy\n"
    )
    with pytest.raises(RuntimeError, match="Unsupported textball format"):
        module.extract_tarball(io.StringIO(legacy), tmp_path / "rejected")
    ####
    module.extract_tarball(io.StringIO(legacy), tmp_path / "accepted", allow_legacy=True)
    assert (tmp_path / "accepted" / "legacy.txt").read_text(encoding="utf-8") == "legacy\n"
####
