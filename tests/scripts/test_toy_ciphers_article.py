"""Round-trip the article's toy transformations; these are not security tests."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ARTICLE = (Path(__file__).resolve().parents[2] / "projects/scripts/toy-ciphers")


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


def _alias_path(tmp_path: Path, target: Path, kind: str) -> Path:
    if kind == "same":
        return target
    ####
    if kind == "relative":
        return Path(target.name)
    ####
    alias = tmp_path / f"{target.stem}-alias{target.suffix}"
    try:
        if kind == "symlink":
            alias.symlink_to(target)
        else:
            os.link(target, alias)
        ####
    except OSError as error:
        pytest.skip(f"{kind} unavailable: {error}")
    ####
    return alias
####


@pytest.mark.parametrize("action", ["encrypt", "decrypt"])
@pytest.mark.parametrize("alias", ["same", "relative", "symlink", "hardlink"])
def test_pcrypt_rejects_input_output_alias(tmp_path: Path, action: str, alias: str) -> None:
    source = tmp_path / "source.txt"
    source.write_text("preserve", encoding="utf-8")
    output = _alias_path(tmp_path, source, alias)
    result = subprocess.run(
        [sys.executable, str(ARTICLE / "pcrypt.py"), action, str(source), "key", str(output)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "different files" in result.stderr
    assert source.read_text(encoding="utf-8") == "preserve"
####


@pytest.mark.parametrize("pair", ["input-output", "input-key", "output-key"])
@pytest.mark.parametrize("alias", ["same", "relative", "symlink", "hardlink"])
def test_otp_encrypt_rejects_aliases(tmp_path: Path, pair: str, alias: str) -> None:
    source = tmp_path / "source.txt"
    output = tmp_path / "output.txt"
    key = tmp_path / "key.txt"
    source.write_text("preserve", encoding="utf-8")
    output.write_text("old output", encoding="utf-8")
    if pair == "input-output":
        output = _alias_path(tmp_path, source, alias)
    elif pair == "input-key":
        key = _alias_path(tmp_path, source, alias)
    else:
        key = _alias_path(tmp_path, output, alias)
    ####
    result = subprocess.run(
        [sys.executable, str(ARTICLE / "otp.py"), "encrypt", str(source), str(output), str(key)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "different files" in result.stderr
    assert source.read_text(encoding="utf-8") == "preserve"
    if pair != "input-output":
        assert output.read_text(encoding="utf-8") == "old output"
    ####
####


@pytest.mark.parametrize("pair", ["input", "key"])
@pytest.mark.parametrize("alias", ["same", "relative", "symlink", "hardlink"])
def test_otp_decrypt_rejects_output_alias(tmp_path: Path, pair: str, alias: str) -> None:
    source = tmp_path / "source.txt"
    key = tmp_path / "key.txt"
    source.write_text("abc", encoding="utf-8")
    key.write_text("AAA", encoding="utf-8")
    output = _alias_path(tmp_path, source if pair == "input" else key, alias)
    result = subprocess.run(
        [sys.executable, str(ARTICLE / "otp.py"), "decrypt", str(source), str(key), str(output)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "output must differ" in result.stderr
    assert source.read_text(encoding="utf-8") == "abc"
    assert key.read_text(encoding="utf-8") == "AAA"
####


def test_otp_encrypt_rejects_same_not_yet_created_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("abc", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ARTICLE / "otp.py"), "encrypt", str(source),
         str(tmp_path / "new.txt"), "new.txt"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "different files" in result.stderr
    assert source.read_text(encoding="utf-8") == "abc"
    assert not (tmp_path / "new.txt").exists()
####


@pytest.mark.parametrize("script", ["otp", "pcrypt"])
def test_toy_ciphers_still_overwrite_distinct_outputs(tmp_path: Path, script: str) -> None:
    source = tmp_path / "source.txt"
    output = tmp_path / "output.txt"
    key = tmp_path / "key.txt"
    source.write_text("abc", encoding="utf-8")
    output.write_text("old", encoding="utf-8")
    key.write_text("old", encoding="utf-8")
    if script == "otp":
        arguments = ["encrypt", str(source), str(output), str(key)]
    else:
        arguments = ["encrypt", str(source), "key", str(output)]
    ####
    result = subprocess.run(
        [sys.executable, str(ARTICLE / f"{script}.py"), *arguments],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert source.read_text(encoding="utf-8") == "abc"
    assert output.read_text(encoding="utf-8") != "old"
    if script == "otp":
        assert len(key.read_text(encoding="utf-8")) == 3
    ####
####


@pytest.mark.parametrize("script", ["otp", "pcrypt"])
def test_toy_ciphers_decrypt_overwrites_distinct_output(tmp_path: Path, script: str) -> None:
    source = tmp_path / "source.txt"
    output = tmp_path / "output.txt"
    key = tmp_path / "key.txt"
    source.write_text("abc", encoding="utf-8")
    key.write_text("AAA", encoding="utf-8")
    output.write_text("old", encoding="utf-8")
    arguments = (["decrypt", str(source), str(key), str(output)] if script == "otp"
                 else ["decrypt", str(source), "key", str(output)])
    result = subprocess.run(
        [sys.executable, str(ARTICLE / f"{script}.py"), *arguments],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert source.read_text(encoding="utf-8") == "abc"
    assert output.read_text(encoding="utf-8") != "old"
####
