"""Exercise the Base64 article's existing CLI with temporary files."""

import base64
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "base64_cli.py"


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
