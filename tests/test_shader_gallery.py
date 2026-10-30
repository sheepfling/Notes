from pathlib import Path

import pytest

from scripts.serve_shader_gallery import (
    is_blocked_request,
    shader_catalog,
    supports_secure_open,
)


@pytest.mark.skipif(not supports_secure_open(), reason="secure descriptor-relative opens unavailable")
def test_shader_catalog_discovers_durable_glsl_and_skips_scratch(tmp_dir: Path) -> None:
    (tmp_dir / "notes" / "aerospace").mkdir(parents=True)
    (tmp_dir / "notes" / "aerospace" / "example.glsl").write_text("void main() {}", encoding="utf-8")
    (tmp_dir / "notes" / "inbox").mkdir()
    (tmp_dir / "notes" / "inbox" / "scratch.glsl").write_text("void main() {}", encoding="utf-8")
    (tmp_dir / "projects" / "shaders").mkdir(parents=True)
    (tmp_dir / "projects" / "shaders" / "point scatterer.glsl").write_text("void main() {}", encoding="utf-8")
    (tmp_dir / "projects" / "shaders" / "artifacts").mkdir()
    (tmp_dir / "projects" / "shaders" / "artifacts" / "render.glsl").write_text("void main() {}", encoding="utf-8")
    (tmp_dir / "artifacts").mkdir()
    (tmp_dir / "artifacts" / "render.glsl").write_text("void main() {}", encoding="utf-8")

    assert shader_catalog(tmp_dir) == [
        {
            "path": "notes/aerospace/example.glsl",
            "url": "/notes/aerospace/example.glsl",
            "name": "example",
        },
        {
            "path": "projects/shaders/point scatterer.glsl",
            "url": "/projects/shaders/point%20scatterer.glsl",
            "name": "point scatterer",
        },
    ]
####


@pytest.mark.skipif(not supports_secure_open(), reason="secure descriptor-relative opens unavailable")
def test_catalog_includes_retained_point_scatterer() -> None:
    root = Path(__file__).resolve().parents[1]
    assert any(
        item["path"] == "projects/shaders/point-scatterer-rcs-shader.glsl"
        for item in shader_catalog(root)
    )
####


def test_gallery_does_not_serve_ignored_paths() -> None:
    assert is_blocked_request("/inbox/raw-note.md")
    assert is_blocked_request("/artifacts/render.png")
    assert is_blocked_request("/.git/config")
    assert not is_blocked_request("/projects/shaders/point-scatterer-rcs-shader.glsl")
####
