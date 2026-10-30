"""Test gallery-related CLI defaults without generating simulation output."""

import runpy
import sys
from pathlib import Path

import pytest

from converging_flow.examples import run_gallery

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "projects/converging-flow/examples"
GALLERY_OUTPUT = Path("artifacts/converging-flow/physics-gallery")


def test_gallery_does_not_treat_unrelated_project_as_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unrelated = tmp_path / "other-project"
    installed = unrelated / ".venv/lib/python3.12/site-packages/converging_flow/examples/run_gallery.py"
    installed.parent.mkdir(parents=True)
    installed.touch()
    (unrelated / "pyproject.toml").touch()
    shadow = unrelated / "src/converging_flow/examples/run_gallery.py"
    shadow.parent.mkdir(parents=True)
    shadow.touch()
    monkeypatch.setattr(run_gallery, "__file__", str(installed))
    assert run_gallery._repository_root() is None
####


@pytest.mark.parametrize("explicit", [False, True])
def test_comparison_routes_inputs_and_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit: bool
) -> None:
    script = EXAMPLES / "physics_diagnostics/pressure_semantics_comparison.py"
    main = runpy.run_module(
        "converging_flow.examples.pressure_semantics_comparison", run_name="comparison_path_test"
    )["main"]
    calls: list[tuple[Path, Path, Path]] = []

    def record_paths(radiant: Path, reactive: Path, output: Path) -> None:
        calls.append((radiant, reactive, output))
    ####

    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(main.__globals__, "build_comparison", record_paths)
    arguments = [str(script)]
    if explicit:
        arguments.extend([
            "--radiant-state", "old/radiant.npz",
            "--reactive-state", "old/reactive.npz",
            "--output", "custom/comparison.png",
        ])
        expected = (Path("old/radiant.npz"), Path("old/reactive.npz"), Path("custom/comparison.png"))
    else:
        expected = (
            GALLERY_OUTPUT / "radiant_1d/radiant_wave_state.npz",
            GALLERY_OUTPUT / "reactive_pressure/reactive_pressure_state.npz",
            GALLERY_OUTPUT / "pressure_semantics_comparison.png",
        )
    ####
    monkeypatch.setattr(sys, "argv", arguments)

    assert main() == 0
    assert calls == [expected]
    assert list(tmp_path.iterdir()) == []
####
