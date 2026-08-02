from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = REPOSITORY_ROOT / "notes" / "development" / "scripts" / "batch"


def run_batch(script: str, *arguments: Path | str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["cmd.exe", "/d", "/c", "call", str(BATCH_ROOT / script), *map(str, arguments)],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_batch_sources_do_not_contain_known_private_identifiers() -> None:
    user_directory = "Us" + "ers"
    forbidden = re.compile(
        r"(?i)(?:\b10\.(?:\d{1,3}\.){2}\d{1,3}\b|"
        r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b|"
        r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b|"
        + rf"[A-Za-z]:\\{user_directory}\\|/mnt/c/{user_directory}/)"
    )
    expected = {
        "README.md",
        "altchar.bat",
        "b64-decode.bat",
        "b64-decode-recursive.bat",
        "b64-encode-recursive.bat",
        "hash-sha256.bat",
        "pack-tar.bat",
        "unpack-tar.bat",
        "untextball.bat",
        "verify-tar.bat",
    }

    assert {path.name for path in BATCH_ROOT.iterdir()} == expected
    for path in BATCH_ROOT.iterdir():
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert forbidden.search(text) is None


@pytest.mark.skipif(os.name != "nt" or shutil.which("cmd.exe") is None, reason="Windows cmd tooling required")
def test_batch_tar_and_base64_transfer_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "hello.txt").write_text("hello from batch\n", encoding="utf-8")
    (source / "bytes.bin").write_bytes(bytes(range(256)))

    archive = tmp_path / "payload.tar"
    unpacked = tmp_path / "unpacked"
    pack = run_batch("pack-tar.bat", source, archive)
    verify = run_batch("verify-tar.bat", archive)
    unpack = run_batch("unpack-tar.bat", archive, unpacked)
    digest = run_batch("hash-sha256.bat", archive)

    assert pack.returncode == 0, pack.stdout + pack.stderr
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert unpack.returncode == 0, unpack.stdout + unpack.stderr
    assert digest.returncode == 0, digest.stdout + digest.stderr
    assert (unpacked / "bytes.bin").read_bytes() == (source / "bytes.bin").read_bytes()

    encoded = tmp_path / "encoded"
    encoded.mkdir()
    for path in source.iterdir():
        shutil.copy2(path, encoded / path.name)
    encode = run_batch("b64-encode-recursive.bat", encoded)

    decoded = tmp_path / "decoded"
    decoded.mkdir()
    for path in encoded.glob("*.b64.txt"):
        shutil.copy2(path, decoded / path.name)
    decode = run_batch("b64-decode-recursive.bat", decoded)

    assert encode.returncode == 0, encode.stdout + encode.stderr
    assert decode.returncode == 0, decode.stdout + decode.stderr
    assert (decoded / "bytes.bin").read_bytes() == (source / "bytes.bin").read_bytes()
