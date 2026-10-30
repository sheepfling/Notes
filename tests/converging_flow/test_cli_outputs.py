"""Verify CLI output destinations and a real temporary-directory run."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from converging_flow.cli import _build_parser

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("command", "required"),
    [
        ("run", ["--dim", "1", "--n", "8"]),
        ("suite", []),
        ("reaction-run", ["--dim", "1", "--n", "8"]),
        ("reaction-suite", []),
        ("radiant-wave-run", ["--dim", "1", "--n", "8"]),
    ],
)
def test_cli_defaults_to_ignored_artifacts_and_accepts_explicit_output(
    command: str, required: list[str], tmp_path: Path
) -> None:
    parser = _build_parser()
    assert parser.parse_args([command, *required]).output == Path("artifacts/converging-flow") / command
    destination = tmp_path / "explicit-output"
    assert parser.parse_args([command, *required, "--output", str(destination)]).output == destination
####


@pytest.mark.parametrize("explicit", [False, True])
def test_cli_run_writes_only_to_requested_temporary_directory(tmp_path: Path, explicit: bool) -> None:
    destination = tmp_path / "custom" if explicit else tmp_path / "artifacts/converging-flow/run"
    command = [
        sys.executable, "-m", "converging_flow", "run", "--dim", "1", "--n", "8",
        "--final-time", "0.001", "--backend", "numpy", "--no-plots",
    ]
    if explicit:
        command.extend(["--output", str(destination)])
    ####
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    environment["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(ROOT / "src"), environment.get("PYTHONPATH", "")) if value
    )
    result = subprocess.run(
        command, cwd=tmp_path, env=environment, capture_output=True, text=True,
        check=False, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((destination / "summary.json").read_text(encoding="utf-8"))
    assert summary["resolved_backend"] == "numpy"
    assert summary["config"]["resolution"] == [8]
    with np.load(destination / "state.npz") as state:
        assert state["pressure"].shape == (8,)
        assert np.isfinite(state["pressure"]).all()
    ####
    assert not (tmp_path / "outputs").exists()
####
