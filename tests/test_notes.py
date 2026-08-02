from pathlib import Path

import scripts.validate_notes as notes_validator
from scripts.validate_notes import Link, check_external, validate


def test_local_markdown_links_are_valid() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    assert validate(repository_root, check_web=False, timeout=10.0) == []


def test_external_connection_errors_are_reported_not_raised(monkeypatch) -> None:
    def fail(*args: Any, **kwargs: Any) -> None:
        raise ConnectionResetError("connection reset during test")

    monkeypatch.setattr(notes_validator, "urlopen", fail)

    error = check_external(Link(Path("note.md"), "https://example.invalid/"), timeout=0.1)

    assert error is not None
    assert "could not be checked" in error
