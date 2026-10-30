"""Smoke-test the real gallery orchestration and its artifact handoffs."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GALLERY = ROOT / "projects/converging-flow/examples/physics_diagnostics/run_gallery.py"

# Keep the gallery's cache under the test directory without replacing any
# simulation, plotting, or child-script stage. The outer process has a timeout.
HARNESS = """
import runpy
import sys
from pathlib import Path

namespace = runpy.run_path(sys.argv[1], run_name="gallery_smoke")
main = namespace["main"]
configure_cache = main.__globals__["configure_backend_cache"]
main.__globals__["configure_backend_cache"] = lambda _root: configure_cache(Path(sys.argv[2]))
raise SystemExit(main(sys.argv[3:]))
"""


def test_gallery_generates_and_connects_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "gallery"
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    env["CUPY_CACHE_DIR"] = str(tmp_path / "cupy-cache")
    env["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(ROOT / "src"), env.get("PYTHONPATH", "")) if value
    )
    result = subprocess.run(
        [
            sys.executable, "-c", HARNESS, str(GALLERY), str(tmp_path),
            "--backend", "numpy", "--one-d-resolution", "8", "--three-d-resolution", "8",
            "--resolution", "8", "--final-time", "0.001", "--frames", "2", "--output", str(output),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"

    for folder, shape in (("radiant_1d", (8,)), ("spherical_shell_3d", (8, 8, 8))):
        directory = output / folder
        summary = json.loads((directory / "radiant_wave_summary.json").read_text(encoding="utf-8"))
        assert summary["resolved_backend"] == "numpy"
        assert summary["config"]["resolution"] == list(shape)
        assert summary["visualization_frames"] == 2
        with np.load(directory / "radiant_wave_state.npz") as state:
            assert state["wave_pressure"].shape == shape
            assert np.isfinite(state["wave_pressure"]).all()
            assert state["coordinate_0"].shape == (8,)
            np.testing.assert_allclose(state["frame_time"], [0.0, 0.001])
            assert state["frame_wave_pressure"].shape[0] == 2
            assert np.isfinite(state["frame_wave_pressure"]).all()
        ####
        with Image.open(directory / "wave_evolution.gif") as animation:
            assert animation.format == "GIF"
            assert animation.n_frames == 2
        ####
    ####

    reactive = output / "reactive_pressure"
    summary = json.loads((reactive / "reactive_pressure_summary.json").read_text(encoding="utf-8"))
    assert summary["resolved_backend"] == "numpy"
    assert summary["resolution"] == 8
    assert summary["frames"] == 2
    with np.load(reactive / "reactive_pressure_state.npz") as state:
        for key in ("coordinate", "pressure", "velocity"):
            assert state[key].shape == (8,)
            assert np.isfinite(state[key]).all()
        ####
        assert state["frame_pressure"].shape == (2, 8)
        assert np.isfinite(state["frame_pressure"]).all()
        np.testing.assert_allclose(state["frame_time"], [0.0, 0.001])
    ####

    comparison = output / "pressure_semantics_comparison.png"
    with Image.open(comparison) as image:
        assert image.format == "PNG"
        assert image.width > 0 and image.height > 0
        image.verify()
    ####
####
