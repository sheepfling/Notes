"""Tests for the retained point-scatterer shader."""

from pathlib import Path


def test_point_scatterer_shader_initializes_complex_accumulator() -> None:
    shader = ((Path(__file__).resolve().parents[1] / "projects/shaders") / "point-scatterer-rcs-shader.glsl").read_text(
        encoding="utf-8"
    )
    assert "vec2 total = vec2(0.0);" in shader
    assert shader.count("{") == shader.count("}")
####
