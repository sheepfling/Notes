from __future__ import annotations

from itertools import pairwise

import numpy as np
import pytest

from converging_flow.config import Dimension, SimulationConfig
from converging_flow.experiment import radial_profile, run_simulation


@pytest.mark.parametrize(
    ("dimensions", "resolution"),
    [(1, 48), (2, 20), (3, 10)],
)
def test_short_run_is_positive_and_conservative(
    dimensions: Dimension,
    resolution: int,
) -> None:
    config = SimulationConfig(
        dimensions=dimensions,
        resolution=(resolution,) * dimensions,
        final_time=0.02,
    )
    result = run_simulation(config)

    assert result.time == pytest.approx(config.final_time)
    assert result.steps > 0
    assert result.final_diagnostics.minimum_density > 0.0
    assert result.final_diagnostics.minimum_pressure > 0.0
    assert result.final_diagnostics.mass == pytest.approx(
        result.initial_diagnostics.mass,
        rel=2.0e-14,
        abs=2.0e-14,
    )
    assert result.final_diagnostics.total_energy == pytest.approx(
        result.initial_diagnostics.total_energy,
        rel=2.0e-14,
        abs=2.0e-14,
    )
####


def test_radial_profile_is_finite() -> None:
    config = SimulationConfig(
        dimensions=2,
        resolution=(24, 24),
        final_time=0.01,
    )
    result = run_simulation(config)
    radius, density, pressure, speed = radial_profile(result, bins=24)

    assert radius.shape == (24,)
    assert np.all(np.isfinite(density))
    assert np.all(np.isfinite(pressure))
    assert np.all(np.isfinite(speed))
####


def test_visualization_frames_are_captured_in_order() -> None:
    config = SimulationConfig(
        dimensions=2,
        resolution=(20, 20),
        final_time=0.02,
    )
    result = run_simulation(config, snapshot_count=5)

    assert len(result.frames) == 5
    assert result.frames[0].time == pytest.approx(0.0)
    assert result.frames[-1].time == pytest.approx(config.final_time)
    assert all(
        earlier.time <= later.time
        for earlier, later in pairwise(result.frames)
    )
    assert result.frames[0].density_field.shape == config.resolution
    assert result.frames[0].radial_profile.radius.shape == (128,)
    assert np.min(result.frames[0].radial_profile.radial_velocity) < 0.0
####


def test_three_dimensional_frames_store_central_slices() -> None:
    config = SimulationConfig(
        dimensions=3,
        resolution=(10, 10, 10),
        final_time=0.01,
    )
    result = run_simulation(config, snapshot_count=3)

    assert len(result.frames) == 3
    assert result.frames[-1].density_field.shape == (10, 10)
    assert result.frames[-1].pressure_field.shape == (10, 10)
####
