"""Exercise the Textball note's CLI and trusted-input safeguards."""

import ast
import base64
import hashlib
import importlib.util
import io
import os
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


def run_textball_in_locale(
    tmp_path: Path, utf8_mode: bool, *arguments: str
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONCOERCECLOCALE": "0",
        "PYTHONUTF8": "1" if utf8_mode else "0",
    })
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=tmp_path, env=env, check=False, capture_output=True, text=True,
    )
####


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize("creator_utf8", [False, True])
def test_explicit_utf8_round_trip_across_locale_modes(
    tmp_path: Path, encoded: bool, creator_utf8: bool
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    content = "café ☃\r\n".encode()
    binary = b"\xff\x80\x00\r\n"
    (source / "text.txt").write_bytes(content)
    (source / "binary.bin").write_bytes(binary)
    package = tmp_path / "package.txt"
    package.touch()
    create_args = ["create", str(source), str(package), "--text", "--encoding", "utf-8"]
    if encoded:
        create_args.append("--encode")
    ####
    created = run_textball_in_locale(tmp_path, creator_utf8, *create_args)
    assert created.returncode == 0, created.stderr

    actual_package = Path(str(package) + ".b64") if encoded else package
    output = tmp_path / "output"
    extract_args = ["extract", str(actual_package), str(output), "--encoding", "utf-8"]
    if encoded:
        extract_args.append("--decode")
    ####
    extracted = run_textball_in_locale(tmp_path, not creator_utf8, *extract_args)
    assert extracted.returncode == 0, extracted.stderr
    assert (output / "source" / "text.txt").read_bytes() == content
    assert (output / "source" / "binary.bin").read_bytes() == binary
    assert (source / "text.txt").read_bytes() == content
####


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize("bom", [False, True])
def test_utf8_sig_preserves_bom_and_bomless_members(tmp_path: Path, encoded: bool, bom: bool) -> None:
    source = tmp_path / "source"
    source.mkdir()
    content = (b"\xef\xbb\xbf" if bom else b"") + "café\r\n".encode()
    (source / "member.txt").write_bytes(content)
    package = tmp_path / "package.txt"
    package.touch()
    create_args = ["create", str(source), str(package), "--text", "--encoding", "utf-8-sig"]
    if encoded:
        create_args.append("--encode")
    ####
    created = run_textball_in_locale(tmp_path, True, *create_args)
    assert created.returncode == 0, created.stderr

    actual_package = Path(str(package) + ".b64") if encoded else package
    archive_text = actual_package.read_text(encoding="utf-8-sig")
    if encoded:
        archive_text = base64.b64decode(archive_text).decode()
    ####
    metadata = ast.literal_eval(archive_text.splitlines()[1].split("\t")[4])
    assert metadata["is_base64"] is (not bom)

    output = tmp_path / "output"
    extract_args = ["extract", str(actual_package), str(output), "--encoding", "utf-8-sig"]
    if encoded:
        extract_args.append("--decode")
    ####
    extracted = run_textball_in_locale(tmp_path, False, *extract_args)
    assert extracted.returncode == 0, extracted.stderr
    assert (output / "source" / "member.txt").read_bytes() == content
    assert (source / "member.txt").read_bytes() == content
####


def test_explicit_legacy_codec_preserves_member_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    content = "café\r\n".encode("cp1252")
    (source / "member.txt").write_bytes(content)
    package = tmp_path / "legacy-codec.txt"
    package.touch()

    created = run_textball_in_locale(
        tmp_path, True, "create", str(source), str(package), "--text", "--encoding", "cp1252"
    )
    output = tmp_path / "output"
    extracted = run_textball_in_locale(
        tmp_path, False, "extract", str(package), str(output), "--encoding", "cp1252"
    )

    assert created.returncode == 0, created.stderr
    assert extracted.returncode == 0, extracted.stderr
    assert (output / "source" / "member.txt").read_bytes() == content
####


@pytest.mark.parametrize("codec", ["not-a-real-codec", "ascii"])
def test_unusable_archive_codec_never_truncates_existing_output(tmp_path: Path, codec: str) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "snowman-☃.txt").write_text("content", encoding="utf-8")
    package = tmp_path / "package.txt"
    package.write_bytes(b"original archive")

    result = run_textball_in_locale(
        tmp_path, True, "create", str(source), str(package), "--text", "--encoding", codec
    )

    assert result.returncode != 0
    assert package.read_bytes() == b"original archive"
    assert (source / "snowman-☃.txt").read_text(encoding="utf-8") == "content"
####


@pytest.mark.parametrize("link_kind", ["symlink", "hardlink"])
def test_create_preserves_distinct_output_link(tmp_path: Path, link_kind: str) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "member.txt").write_bytes(b"input bytes\n")
    target = tmp_path / "existing.txt"
    target.write_bytes(b"old archive")
    package = tmp_path / "package.txt"
    try:
        if link_kind == "symlink":
            package.symlink_to(target)
        else:
            os.link(target, package)
        ####
    except OSError as error:
        pytest.skip(f"{link_kind} unavailable: {error}")
    ####
    original_inode = target.stat().st_ino

    result = run_textball(tmp_path, "create", str(source), str(package), "--encoding", "utf-8")

    assert result.returncode == 0, result.stderr
    assert package.samefile(target)
    assert target.stat().st_ino == original_inode
    assert package.is_symlink() == (link_kind == "symlink")
    assert target.read_bytes().startswith(b"NOTES-TEXTBALL/1\n")
    assert (source / "member.txt").read_bytes() == b"input bytes\n"
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
    digest = hashlib.md5(b"legacy\n").hexdigest()
    legacy = (
        "'legacy.txt'\t1\t0\t1\t"
        "{'path': 'legacy.txt', 'num_lines': 1, 'is_base64': False, "
        "'has_trailing_newline': True, 'file_size': 7, "
        f"'md5': '{digest}'}}\n"
        "legacy\n"
    )
    with pytest.raises(RuntimeError, match="Unsupported textball format"):
        module.extract_tarball(io.StringIO(legacy), tmp_path / "rejected")
    ####
    module.extract_tarball(io.StringIO(legacy), tmp_path / "accepted", allow_legacy=True)
    assert (tmp_path / "accepted" / "legacy.txt").read_text(encoding="utf-8") == "legacy\n"
####


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize("corruption", ["payload", "size"])
def test_corrupt_member_never_overwrites_existing_destination(
    tmp_path: Path, encoded: bool, corruption: str
) -> None:
    module = load_textball("textball_corruption")
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source = source_dir / "member.txt"
    source.write_bytes(b"hello\n")
    stream = io.StringIO()
    module.write_tarball(source_dir, stream, encode_all=encoded)
    lines = stream.getvalue().splitlines(keepends=True)
    if corruption == "payload":
        lines[2] = ("A" if lines[2][0] != "A" else "B") + lines[2][1:]
    else:
        header = lines[1].split("\t")
        metadata = ast.literal_eval(header[4])
        metadata["file_size"] += 1
        header[4] = repr(metadata) + "\n"
        lines[1] = "\t".join(header)
    ####
    package = tmp_path / "corrupt.txt"
    package.write_text("".join(lines), encoding="utf-8")
    target = tmp_path / "output" / source_dir.name / source.name
    target.parent.mkdir(parents=True)
    target.write_bytes(b"preserve existing output")

    result = run_textball(tmp_path, "extract", str(package), str(target.parents[1]))

    assert result.returncode != 0
    assert ("Checksum mismatch" if corruption == "payload" else "Invalid size") in result.stderr
    assert "extracted to" not in result.stdout
    assert target.read_bytes() == b"preserve existing output"
    assert source.read_bytes() == b"hello\n"
####


@pytest.mark.parametrize("encoded", [False, True])
def test_valid_member_can_overwrite_distinct_existing_destination(tmp_path: Path, encoded: bool) -> None:
    module = load_textball("textball_valid_overwrite")
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "member.txt").write_bytes(b"hello\n")
    stream = io.StringIO()
    module.write_tarball(source_dir, stream, encode_all=encoded)
    output = tmp_path / "output"
    target = output / "source" / "member.txt"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"old contents")

    module.extract_tarball(io.StringIO(stream.getvalue()), output)

    assert target.read_bytes() == b"hello\n"
####


def test_text_extraction_preserves_unicode_and_crlf_bytes(tmp_path: Path) -> None:
    module = load_textball("textball_text_newlines")
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    content = "café\r\nnext line\r\n".encode()
    (source_dir / "member.txt").write_bytes(content)
    stream = io.StringIO()
    module.write_tarball(source_dir, stream, encode_all=False)

    output = tmp_path / "output"
    module.extract_tarball(io.StringIO(stream.getvalue()), output)

    assert (output / "source" / "member.txt").read_bytes() == content
####


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize(
    "content",
    [b"first\r\nsecond\r\n", b"first\r\nsecond", b"ends in carriage return\r", b"\x00\xff\x80\r\n\x03"],
)
def test_cli_text_round_trip_preserves_newlines(tmp_path: Path, encoded: bool, content: bytes) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "member.txt").write_bytes(content)
    package = tmp_path / "package.txt"
    package.touch()
    create_args = ["create", str(source), str(package), "--text"]
    if encoded:
        create_args.append("--encode")
    ####
    created = run_textball(tmp_path, *create_args)
    actual_package = Path(str(package) + ".b64") if encoded else package
    output = tmp_path / "output"
    extract_args = ["extract", str(actual_package), str(output)]
    if encoded:
        extract_args.append("--decode")
    ####
    extracted = run_textball(tmp_path, *extract_args)

    assert created.returncode == 0, created.stderr
    assert extracted.returncode == 0, extracted.stderr
    assert (output / "source" / "member.txt").read_bytes() == content
    assert (source / "member.txt").read_bytes() == content
####


@pytest.mark.parametrize("content", [b"first\nsecond", b"first\r\nsecond\r\n", b"ends in carriage return\r"])
def test_cli_accepts_matching_historical_windows_newlines(tmp_path: Path, content: bytes) -> None:
    module = load_textball("textball_windows_archive")
    source = tmp_path / "source"
    source.mkdir()
    (source / "member.txt").write_bytes(content)
    stream = io.StringIO()
    module.write_tarball(source, stream, encode_all=False)
    package = tmp_path / "legacy-windows.txt"
    package.write_bytes(stream.getvalue().replace("\n", "\r\n").encode())
    output = tmp_path / "output"

    result = run_textball(tmp_path, "extract", str(package), str(output))

    assert result.returncode == 0, result.stderr
    assert (output / "source" / "member.txt").read_bytes() == content
####


@pytest.mark.parametrize("alias_kind", ["same", "symlink", "hardlink"])
def test_cli_never_overwrites_its_input_archive(tmp_path: Path, alias_kind: str) -> None:
    payload = b"replacement\n"
    digest = hashlib.md5(payload).hexdigest()
    member_name = "package.txt" if alias_kind == "same" else "alias.txt"
    metadata = {
        "path": member_name,
        "num_lines": 1,
        "is_base64": False,
        "has_trailing_newline": True,
        "file_size": len(payload),
        "md5": digest,
    }
    package = tmp_path / "package.txt"
    package.write_text(
        "NOTES-TEXTBALL/1\n"
        + f"{member_name!r}\t1\t0\t1\t{metadata!r}\n"
        + payload.decode(),
        encoding="utf-8",
    )
    before = package.read_bytes()
    alias = tmp_path / "alias.txt"
    try:
        if alias_kind == "symlink":
            alias.symlink_to(package)
        elif alias_kind == "hardlink":
            os.link(package, alias)
        ####
    except OSError as error:
        pytest.skip(f"{alias_kind} unavailable: {error}")
    ####

    result = run_textball(tmp_path, "extract", str(package), str(tmp_path))

    assert result.returncode != 0
    assert "Output aliases the input textball" in result.stderr
    assert "extracted to" not in result.stdout
    assert package.read_bytes() == before
####
