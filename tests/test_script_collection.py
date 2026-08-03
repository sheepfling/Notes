import base64
import importlib.util
import io
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "projects" / "scripts"
SCRIPT_PATHS = {
    "altchar.py": Path("altchar") / "altchar.py",
    "base64_cli.py": Path("base64") / "base64_cli.py",
    "find_and_pull_all_git.py": Path("git-maintenance") / "find_and_pull_all_git.py",
    "otp.py": Path("toy-ciphers") / "otp.py",
    "pcrypt.py": Path("toy-ciphers") / "pcrypt.py",
    "readlines.py": Path("readlines") / "readlines.py",
    "textball.py": Path("textball") / "textball.py",
}


def run_script(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_ROOT / SCRIPT_PATHS[script]), *arguments],
        cwd=SCRIPT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
####


def load_script_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_ROOT / SCRIPT_PATHS[filename])
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
####


def test_altchar_round_trip_for_single_line(tmp_dir: Path) -> None:
    source = tmp_dir / "source.txt"
    inserted = tmp_dir / "inserted.txt"
    restored = tmp_dir / "restored.txt"
    source.write_text("abcd", encoding="utf-8")

    insert = run_script("altchar.py", "insert", str(source), "--char", "A", "--output", str(inserted))
    remove = run_script("altchar.py", "remove", str(inserted), "--char", "A", "--output", str(restored))

    assert insert.returncode == 0, insert.stderr
    assert remove.returncode == 0, remove.stderr
    assert inserted.read_text(encoding="utf-8") == "aAbAcAdA"
    assert restored.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
####


def test_altchar_round_trip_for_multiline_input(tmp_dir: Path) -> None:
    source = tmp_dir / "source.txt"
    inserted = tmp_dir / "inserted.txt"
    restored = tmp_dir / "restored.txt"
    source.write_text("ab\ncd\n", encoding="utf-8")

    assert run_script("altchar.py", "insert", str(source), "--char", "A", "--output", str(inserted)).returncode == 0
    assert run_script("altchar.py", "remove", str(inserted), "--char", "A", "--output", str(restored)).returncode == 0
    assert restored.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
####


def test_base64_cli_round_trip(tmp_dir: Path) -> None:
    source = tmp_dir / "source.bin"
    encoded = tmp_dir / "source.b64"
    restored = tmp_dir / "restored.bin"
    source.write_bytes(bytes(range(256)))

    encode = run_script("base64_cli.py", "encode", str(source), str(encoded))
    decode = run_script("base64_cli.py", "decode", str(encoded), str(restored))

    assert encode.returncode == 0, encode.stderr
    assert decode.returncode == 0, decode.stderr
    assert restored.read_bytes() == source.read_bytes()
####


def test_textball_round_trip_text_and_binary(tmp_dir: Path) -> None:
    source_dir = tmp_dir / "input"
    output_dir = tmp_dir / "output"
    package = tmp_dir / "package.txt"
    source_dir.mkdir()
    (source_dir / "hello.txt").write_text("hello\n", encoding="utf-8")
    (source_dir / "bytes.bin").write_bytes(bytes(range(32)))
    package.touch()

    create = run_script("textball.py", "create", str(source_dir), str(package), "--encode")
    encoded_package = Path(str(package) + ".b64")
    extract = run_script("textball.py", "extract", str(encoded_package), str(output_dir), "--decode")

    assert create.returncode == 0, create.stderr
    assert extract.returncode == 0, extract.stderr
    decoded_text = base64.b64decode(encoded_package.read_text(encoding='utf-8')).decode()
    assert decoded_text.startswith('NOTES-TEXTBALL/1\n')
    assert (output_dir / source_dir.name / "hello.txt").read_text(encoding="utf-8") == "hello\n"
    assert (output_dir / source_dir.name / "bytes.bin").read_bytes() == bytes(range(32))
####


def test_textball_rejects_unknown_format_and_traversal(tmp_dir: Path) -> None:
    module = load_script_module("textball_safety", "textball.py")
    output_dir = tmp_dir / "output"

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


def test_textball_legacy_requires_explicit_opt_in(tmp_dir: Path) -> None:
    module = load_script_module("textball_legacy", "textball.py")
    legacy = (
        "'legacy.txt'\t1\t0\t1\t"
        "{'path': 'legacy.txt', 'num_lines': 1, 'is_base64': False, "
        "'has_trailing_newline': True, 'file_size': 7, 'md5': 'invalid'}\n"
        "legacy\n"
    )
    with pytest.raises(RuntimeError, match="Unsupported textball format"):
        module.extract_tarball(io.StringIO(legacy), tmp_dir / "rejected")
    ####
    module.extract_tarball(io.StringIO(legacy), tmp_dir / "accepted", allow_legacy=True)
    assert (tmp_dir / "accepted" / "legacy.txt").read_text(encoding="utf-8") == "legacy\n"
####


def test_git_script_discovers_normal_and_bare_repositories(tmp_dir: Path) -> None:
    module = load_script_module("find_and_pull_all_git", "find_and_pull_all_git.py")
    normal = tmp_dir / "normal" / ".git"
    bare = tmp_dir / "bare.git"
    normal.mkdir(parents=True)
    (bare / "config").parent.mkdir(parents=True)
    (bare / "config").write_text("[core]\n\tbare = true\n", encoding="utf-8")
    (bare / "head").write_text("ref: refs/heads/main\n", encoding="utf-8")

    found = set(module.find_git_repos(tmp_dir))

    assert tmp_dir / "normal" in found
    assert bare in found
####


def test_git_script_uses_non_destructive_update_commands(tmp_dir: Path) -> None:
    module = load_script_module("find_and_pull_commands", "find_and_pull_all_git.py")

    commands = module.update_commands(tmp_dir / "repo", bare=False)

    assert [part for command in commands for part in command if part in {"reset", "clean", "checkout"}] == []
    assert commands[-1][-2:] == ["pull", "--ff-only"]
####


def test_otp_round_trip_preserves_newlines_and_unicode() -> None:
    module = load_script_module("otp", "otp.py")
    source = "hello\nworld — café"
    key = module.make_otp(len(source))

    transformed = module.add_otp(source, key)

    assert module.sub_otp(transformed, key) == source
####


def test_otp_rejects_key_length_mismatch() -> None:
    module = load_script_module("otp_length", "otp.py")

    try:
        module.add_otp("abc", "ke")
    except ValueError as error:
        assert "lengths differ" in str(error)
    else:
        raise AssertionError("a key length mismatch must be rejected")
    ####
####


def test_repeating_passphrase_round_trip_and_empty_key_rejection() -> None:
    module = load_script_module("pcrypt", "pcrypt.py")
    source = "hello\nworld — café"

    assert module.sub_passphrase(module.add_passphrase(source, "key"), "key") == source
    try:
        module.add_passphrase(source, "")
    except ValueError as error:
        assert "cannot be empty" in str(error)
    else:
        raise AssertionError("an empty passphrase must be rejected")
    ####
####


def test_readlines_represents_line_endings(tmp_dir: Path) -> None:
    module = load_script_module("readlines", "readlines.py")
    source = tmp_dir / "lines.txt"
    source.write_text("one\nlast", encoding="utf-8", newline="")

    assert module.represented_lines(source) == ["0: 'one\\n'", "1: 'last'"]
####
