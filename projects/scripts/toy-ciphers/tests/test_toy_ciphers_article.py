"""Round-trip the article's toy transformations; these are not security tests."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ARTICLE = Path(__file__).resolve().parents[1]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ARTICLE / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
####


def test_otp_round_trip_preserves_newlines_and_unicode() -> None:
    module = load_script("otp")
    source = "hello\nworld — café"
    key = module.make_otp(len(source))
    assert module.sub_otp(module.add_otp(source, key), key) == source
####


def test_otp_rejects_key_length_mismatch() -> None:
    module = load_script("otp")
    with pytest.raises(ValueError, match="lengths differ"):
        module.add_otp("abc", "ke")
    ####
####


def test_repeating_passphrase_round_trip_and_empty_key_rejection() -> None:
    module = load_script("pcrypt")
    source = "hello\nworld — café"
    assert module.sub_passphrase(module.add_passphrase(source, "key"), "key") == source
    with pytest.raises(ValueError, match="cannot be empty"):
        module.add_passphrase(source, "")
    ####
####


@pytest.mark.parametrize("script", ["otp", "pcrypt"])
@pytest.mark.parametrize("original", ["hello\nworld — café\n", "hello\r\nworld — café\r\n"])
def test_cli_outputs_stay_in_requested_temporary_paths(tmp_path: Path, script: str, original: str) -> None:
    source = tmp_path / "source.txt"
    transformed = tmp_path / "transformed.txt"
    restored = tmp_path / "restored.txt"
    key = tmp_path / "key.txt"
    original_bytes = original.encode("utf-8")
    source.write_bytes(original_bytes)
    if script == "otp":
        commands = [("encrypt", str(source), str(transformed), str(key)),
                    ("decrypt", str(transformed), str(key), str(restored))]
        expected_files = {"source.txt", "transformed.txt", "restored.txt", "key.txt"}
    else:
        commands = [("encrypt", str(source), "key", str(transformed)),
                    ("decrypt", str(transformed), "key", str(restored))]
        expected_files = {"source.txt", "transformed.txt", "restored.txt"}
    ####
    for arguments in commands:
        result = subprocess.run(
            [sys.executable, str(ARTICLE / f"{script}.py"), *arguments],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    ####
    assert source.read_bytes() == original_bytes
    assert restored.read_bytes() == original_bytes
    assert {path.name for path in tmp_path.iterdir()} == expected_files
####
