"""Exercise animation scheduling without opening a browser or GPU context."""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_slider_redraw_keeps_one_animation_loop() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for the shader-gallery JavaScript test")
    ####
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            node,
            str(root / "tests/shader_gallery_animation_test.cjs"),
            str(root / "projects/shaders/shader-gallery/shader-gallery.js"),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
####
