"""Compatibility entry point for converging_flow.examples.reactive_pressure_demo."""

import sys as _sys
from pathlib import Path as _Path

_source_root = _Path(__file__).resolve().parents[4] / "src"
if str(_source_root) not in _sys.path:
    _sys.path.insert(0, str(_source_root))
####
_implementation = _source_root / "converging_flow" / "examples" / "reactive_pressure_demo.py"
# Execute the fixed repository-owned module in this legacy module's namespace,
# preserving imports, monkeypatching, and historical __file__ behavior.
exec(compile(_implementation.read_bytes(), str(_implementation), "exec"), globals())  # noqa: S102
