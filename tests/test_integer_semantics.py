"""Compatibility entrypoint for the integer lab's co-located tests."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_test_path = Path(__file__).resolve().parents[1] / "projects/integer-semantics-lab/tests/test_integer_semantics_project.py"
_spec = spec_from_file_location("_integer_semantics_project_tests_compat", _test_path)
assert _spec is not None and _spec.loader is not None
_module = module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
for _name in dir(_module):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_module, _name)
    ####
####
