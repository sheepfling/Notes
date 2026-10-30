#!/usr/bin/env python3
"""Compatibility entry point for the shared implementation."""

from pathlib import Path as _Path

# Execute the shared source in this module's namespace so existing imports and
# monkeypatches retain their historical behavior, including its __file__ path.
_shared_source = _Path(__file__).resolve().parents[3] / "src" / "notes_tools" / "integer_semantics/compare_reports.py"
exec(compile(_shared_source.read_bytes(), str(_shared_source), "exec"))
