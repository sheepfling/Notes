"""Compatibility entrypoint for the shader collection's co-located tests."""

import runpy
from pathlib import Path

_test_path = Path(__file__).resolve().parents[1] / "projects/shaders/tests/test_shader_project.py"
test_point_scatterer_shader_initializes_complex_accumulator = runpy.run_path(str(_test_path))[
    "test_point_scatterer_shader_initializes_complex_accumulator"
]
