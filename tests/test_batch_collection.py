from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = REPOSITORY_ROOT / "projects" / "scripts"
BATCH_PATHS = {
    "altchar.bat": Path("altchar") / "altchar.bat",
    "b64-decode.bat": Path("base64") / "b64-decode.bat",
    "b64-decode-recursive.bat": Path("base64") / "b64-decode-recursive.bat",
    "b64-encode-recursive.bat": Path("base64") / "b64-encode-recursive.bat",
    "hash-sha256.bat": Path("transfer-bundle") / "hash-sha256.bat",
    "pack-transfer.bat": Path("transfer-bundle") / "pack-transfer.bat",
    "pack-tar.bat": Path("transfer-bundle") / "pack-tar.bat",
    "unpack-transfer.bat": Path("transfer-bundle") / "unpack-transfer.bat",
    "unpack-tar.bat": Path("transfer-bundle") / "unpack-tar.bat",
    "untextball.bat": Path("textball") / "untextball.bat",
    "verify-tar.bat": Path("transfer-bundle") / "verify-tar.bat",
}


def run_batch(script: str, *arguments: Path | str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["cmd.exe", "/d", "/c", "call", str(BATCH_ROOT / BATCH_PATHS[script]), *map(str, arguments)],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
####


def test_batch_sources_do_not_contain_known_private_identifiers() -> None:
    user_directory = "Us" + "ers"
    forbidden = re.compile(
        r"(?i)(?:\b10\.(?:\d{1,3}\.){2}\d{1,3}\b|"
        r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b|"
        r"\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b|"
        + rf"[A-Za-z]:\\{user_directory}\\|/mnt/c/{user_directory}/)"
    )
    expected = {
        "altchar.bat",
        "b64-decode.bat",
        "b64-decode-recursive.bat",
        "b64-encode-recursive.bat",
        "hash-sha256.bat",
        "pack-transfer.bat",
        "pack-tar.bat",
        "unpack-transfer.bat",
        "unpack-tar.bat",
        "untextball.bat",
        "verify-tar.bat",
    }

    assert set(BATCH_PATHS) == expected
    for relative_path in BATCH_PATHS.values():
        path = BATCH_ROOT / relative_path
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert forbidden.search(text) is None
        ####
    ####
####


@pytest.mark.skipif(os.name != "nt" or shutil.which("cmd.exe") is None, reason="Windows cmd tooling required")
def test_batch_tar_and_base64_transfer_round_trip(tmp_dir: Path) -> None:
    source = tmp_dir / "source"
    source.mkdir()
    (source / "hello.txt").write_text("hello from batch\n", encoding="utf-8")
    (source / "bytes.bin").write_bytes(bytes(range(256)))

    archive = tmp_dir / "payload.tar"
    unpacked = tmp_dir / "unpacked"
    pack = run_batch("pack-tar.bat", source, archive)
    verify = run_batch("verify-tar.bat", archive)
    unpack = run_batch("unpack-tar.bat", archive, unpacked)
    digest = run_batch("hash-sha256.bat", archive)

    assert pack.returncode == 0, pack.stdout + pack.stderr
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert unpack.returncode == 0, unpack.stdout + unpack.stderr
    assert digest.returncode == 0, digest.stdout + digest.stderr
    assert (unpacked / "bytes.bin").read_bytes() == (source / "bytes.bin").read_bytes()

    encoded = tmp_dir / "encoded"
    encoded.mkdir()
    for path in source.iterdir():
        shutil.copy2(path, encoded / path.name)
    ####
    encode = run_batch("b64-encode-recursive.bat", encoded)

    decoded = tmp_dir / "decoded"
    decoded.mkdir()
    for path in encoded.glob("*.b64.txt"):
        shutil.copy2(path, decoded / path.name)
    ####
    decode = run_batch("b64-decode-recursive.bat", decoded)

    assert encode.returncode == 0, encode.stdout + encode.stderr
    assert decode.returncode == 0, decode.stdout + decode.stderr
    assert (decoded / "bytes.bin").read_bytes() == (source / "bytes.bin").read_bytes()
####


@pytest.mark.skipif(os.name != "nt" or shutil.which("cmd.exe") is None, reason="Windows cmd tooling required")
def test_batch_altchar_round_trip(tmp_dir: Path) -> None:
    source = tmp_dir / "source.txt"
    inserted = tmp_dir / "inserted.txt"
    restored = tmp_dir / "restored.txt"
    source.write_text("abc\nxyz\n", encoding="utf-8", newline="")

    insert = run_batch("altchar.bat", "insert", source, "_", inserted)
    remove = run_batch("altchar.bat", "remove", inserted, "_", restored)

    assert insert.returncode == 0, insert.stdout + insert.stderr
    assert remove.returncode == 0, remove.stdout + remove.stderr
    assert inserted.read_text(encoding="utf-8").splitlines() == ["a_b_c_", "x_y_z_"]
    assert restored.read_text(encoding="utf-8").splitlines() == ["abc", "xyz"]
####


@pytest.mark.skipif(
    os.name != "nt" or shutil.which("certutil.exe") is None,
    reason="Windows certutil tooling required",
)
def test_batch_base64_decode_round_trip(tmp_dir: Path) -> None:
    payload = bytes(range(256))
    encoded = tmp_dir / "payload.b64"
    decoded = tmp_dir / "payload.bin"
    encoded.write_bytes(base64.encodebytes(payload))

    result = run_batch("b64-decode.bat", encoded, decoded)

    assert result.returncode == 0, result.stdout + result.stderr
    assert decoded.read_bytes() == payload
####


@pytest.mark.skipif(os.name != "nt" or shutil.which("cmd.exe") is None, reason="Windows cmd tooling required")
def test_batch_untextball_extracts_line_oriented_file(tmp_dir: Path) -> None:
    package = tmp_dir / "package.txt"
    output_directory = tmp_dir / "extracted"
    package.write_text(
        'NOTES-TEXTBALL/1\n"hello.txt"\t2\t0\t1\t{}\nfirst line\nsecond line\n',
        encoding="utf-8",
        newline="",
    )

    result = run_batch("untextball.bat", package, output_directory)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (output_directory / "hello.txt").read_text(encoding="utf-8").splitlines() == [
        "first line",
        "second line",
    ]
####


@pytest.mark.skipif(os.name != "nt" or shutil.which("cmd.exe") is None, reason="Windows cmd tooling required")
def test_batch_untextball_rejects_unmarked_and_traversal_input(tmp_dir: Path) -> None:
    unmarked = tmp_dir / "unmarked.txt"
    unmarked.write_text('"hello.txt"\t1\t0\t1\t{}\nhello\n', encoding="utf-8", newline="")
    rejected = run_batch("untextball.bat", unmarked, tmp_dir / "unmarked-output")
    assert rejected.returncode != 0

    traversal = tmp_dir / "traversal.txt"
    traversal.write_text(
        'NOTES-TEXTBALL/1\n"..\\escape.txt"\t1\t0\t1\t{}\nhello\n',
        encoding="utf-8",
        newline="",
    )
    blocked = run_batch("untextball.bat", traversal, tmp_dir / "traversal-output")
    assert blocked.returncode != 0
    assert not (tmp_dir / "escape.txt").exists()
####


@pytest.mark.skipif(os.name != "nt" or shutil.which("tar.exe") is None, reason="Windows tar tooling required")
def test_batch_transfer_bundle_round_trip(tmp_dir: Path) -> None:
    source = tmp_dir / "source"
    source.mkdir()
    (source / "hello.txt").write_text("hello from transfer\n", encoding="utf-8")
    (source / "nested").mkdir()
    (source / "nested" / "bytes.bin").write_bytes(bytes(range(64)))

    prefix = tmp_dir / "payload"
    pack = run_batch("pack-transfer.bat", source, prefix)
    archive = Path(str(prefix) + ".tar.gz")
    encoded = Path(str(archive) + ".b64.txt")
    hash_file = Path(str(archive) + ".sha256")
    manifest = Path(str(archive) + ".manifest.txt")

    assert pack.returncode == 0, pack.stdout + pack.stderr
    assert archive.is_file()
    assert encoded.is_file()
    assert hash_file.is_file()
    assert manifest.read_text(encoding="utf-8").splitlines() == [
        "NOTES-TRANSFER/1",
        "archive=tar.gz",
        "encoding=certutil-base64",
        f"sha256={hash_file.read_text(encoding='ascii').strip()}",
    ]
    assert re.fullmatch(r"[0-9a-fA-F]{64}\s*", hash_file.read_text(encoding="ascii"))

    output = tmp_dir / "unpacked-from-existing-archive"
    unpack = run_batch("unpack-transfer.bat", encoded, output)

    assert unpack.returncode == 0, unpack.stdout + unpack.stderr
    assert (output / "hello.txt").read_text(encoding="utf-8") == "hello from transfer\n"
    assert (output / "nested" / "bytes.bin").read_bytes() == bytes(range(64))

    archive.unlink()
    decoded_output = tmp_dir / "unpacked-from-transfer-text"
    decoded = run_batch("unpack-transfer.bat", encoded, decoded_output)

    assert decoded.returncode == 0, decoded.stdout + decoded.stderr
    assert (decoded_output / "hello.txt").read_text(encoding="utf-8") == "hello from transfer\n"
    assert (decoded_output / "nested" / "bytes.bin").read_bytes() == bytes(range(64))

    hash_file.write_text("0" * 64 + "\n", encoding="ascii")
    rejected_output = tmp_dir / "rejected"
    rejected = run_batch("unpack-transfer.bat", encoded, rejected_output)

    assert rejected.returncode != 0
    assert not rejected_output.exists()
####
