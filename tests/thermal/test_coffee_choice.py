"""Check the coffee-choice model, reproduction command and recorded invariants."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from notes.thermal.coffee_choice import Parameters, compare, cool, mix


def test_recorded_default_and_warm_creamer() -> None:
    early, late = compare(Parameters())
    assert early == pytest.approx(33.05, abs=0.005)
    assert late == pytest.approx(31.57, abs=0.005)
    assert late - early == pytest.approx(-1.49, abs=0.005)

    early, late = compare(Parameters(creamer_c=70.0))
    assert early == pytest.approx(34.44, abs=0.005)
    assert late == pytest.approx(34.58, abs=0.005)
    assert late - early == pytest.approx(0.14, abs=0.005)
####


def test_instant_addition_gives_equal_results() -> None:
    early, late = compare(Parameters(add_later_s=0.0))
    assert early == pytest.approx(late)
####


def test_cooling_and_mixing_obey_model() -> None:
    assert cool(90, 20, 1045, 3, 0) == pytest.approx(90)
    assert mix(80, 20, 4, 1) == pytest.approx(68)
    with pytest.raises(ValueError):
        compare(Parameters(add_later_s=601))
    ####
####


def test_module_reproduction_prints_results_without_artifacts(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(root), environment.get("PYTHONPATH", "")) if value
    )
    result = subprocess.run(
        [sys.executable, "-m", "notes.thermal.coffee_choice"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "Cold creamer (5 °C): now 33.05 °C; later 31.57 °C" in result.stdout
    assert "Warm creamer (70 °C): now 34.44 °C; later 34.58 °C" in result.stdout
    assert not list(tmp_path.iterdir())
####
