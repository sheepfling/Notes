from pathlib import Path


def test_point_scatterer_shader_initializes_complex_accumulator() -> None:
    shader = Path("notes/development/shaders/point-scatterer-rcs-shader.glsl").read_text(
        encoding="utf-8"
    )
    assert "vec2 total = vec2(0.0);" in shader
    assert shader.count("{") == shader.count("}")
