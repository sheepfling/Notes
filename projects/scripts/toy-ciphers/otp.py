"""Compatibility entry point for the shared otp implementation."""

from pathlib import Path as _CompatibilityPath

# Run the trusted source from this checkout in the legacy module namespace.
# This preserves __file__, imports, runpy, and callers patching module globals.
_compatibility_source = (
    _CompatibilityPath(__file__).resolve().parents[3]
    / "src" / "notes_tools" / "articles" / "otp.py"
)
exec(compile(_compatibility_source.read_bytes(), str(_compatibility_source), "exec"), globals())  # noqa: S102
