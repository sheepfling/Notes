"""Exercise the transfer unpacker's failure handling with temporary files."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

UNPACKER = Path(__file__).resolve().parents[1] / "unpack-transfer.bat"


@pytest.mark.skipif(
    os.name != "nt" or shutil.which("cmd.exe") is None,
    reason="Windows command tooling required",
)
@pytest.mark.parametrize("already_decoded", [True, False])
def test_hash_failure_only_removes_newly_decoded_archive(
    tmp_path: Path, already_decoded: bool
) -> None:
    # Replace external decode/hash commands in a temporary copy to exercise
    # cleanup deterministically without modifying the original script.
    original = UNPACKER.read_text(encoding="utf-8")
    hash_command = 'certutil.exe -hashfile "%ARCHIVE%" SHA256'
    decode_command = 'certutil.exe -decode "%ENCODED%" "%ARCHIVE%" >nul'
    assert original.count(hash_command) == 1
    assert original.count(decode_command) == 1
    faulted = tmp_path / "unpack-transfer-faulted.bat"
    faulted.write_text(
        original.replace(hash_command, "cmd.exe /d /c exit 1").replace(
            decode_command, 'copy /y "%ENCODED%" "%ARCHIVE%" >nul'
        ),
        encoding="utf-8",
        newline="\r\n",
    )

    archive = tmp_path / "payload.tar.gz"
    encoded = tmp_path / "payload.tar.gz.b64.txt"
    output = tmp_path / "output"
    original_archive = b"existing archive must survive"
    if already_decoded:
        archive.write_bytes(original_archive)
    ####
    encoded.write_text("placeholder", encoding="ascii")

    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "call", str(faulted), str(encoded), str(output), "--legacy"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SHA-256 calculation failed." in result.stdout
    if already_decoded:
        assert archive.read_bytes() == original_archive
    else:
        assert not archive.exists()
    ####
    assert encoded.read_text(encoding="ascii") == "placeholder"
    assert not output.exists()
####
