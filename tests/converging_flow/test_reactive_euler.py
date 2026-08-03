from __future__ import annotations

import numpy as np

from converging_flow.backend import get_array_backend
from converging_flow.reactive_euler import (
    ReactiveEulerConfig,
    advance_reactive_euler_split,
    apply_reaction_source,
    primitive_to_reactive_conservative,
    reactive_conservative_to_primitive,
)


def _uniform_reactive_state(size: int = 96) -> tuple[object, object, ReactiveEulerConfig]:
    backend = get_array_backend("numpy")
    config = ReactiveEulerConfig(gamma=1.4, heat_release_per_mass=2.0)
    density = np.ones(size, dtype=np.float64)
    velocity = np.zeros((1, size), dtype=np.float64)
    pressure = np.ones(size, dtype=np.float64)
    progress = np.zeros(size, dtype=np.float64)
    state = primitive_to_reactive_conservative(
        density,
        velocity,
        pressure,
        progress,
        config,
        backend,
    )
    return backend, state, config
####


def test_reaction_source_advances_progress_and_eos_pressure() -> None:
    backend, state, config = _uniform_reactive_state(32)
    progress_rate = np.full(32, 0.25, dtype=np.float64)

    updated = apply_reaction_source(
        state,
        progress_rate,
        force_density=None,
        timestep=0.4,
        config=config,
        backend=backend,
    )
    _density, velocity, pressure, progress = reactive_conservative_to_primitive(
        updated,
        config,
        backend,
    )

    assert np.allclose(progress, 0.1)
    assert np.allclose(velocity, 0.0)
    assert np.allclose(
        pressure,
        1.0 + (config.gamma - 1.0) * config.heat_release_per_mass * 0.1,
    )
####


def test_local_heat_release_creates_pressure_gradient_and_motion() -> None:
    backend, state, config = _uniform_reactive_state(128)
    coordinate = np.linspace(-1.0, 1.0, 128, dtype=np.float64)
    progress_rate = 4.0 * np.exp(-80.0 * coordinate * coordinate)
    timestep = 2.0e-3

    updated = advance_reactive_euler_split(
        state,
        progress_rate,
        force_density=None,
        timestep=timestep,
        spacing=(coordinate[1] - coordinate[0],),
        config=config,
        backend=backend,
    )
    _density, velocity, pressure, progress = reactive_conservative_to_primitive(
        updated,
        config,
        backend,
    )

    midpoint = coordinate.size // 2
    assert float(np.max(pressure)) > 1.0
    assert float(np.max(progress)) > 0.0
    assert float(np.min(velocity[0, :midpoint])) < 0.0
    assert float(np.max(velocity[0, midpoint:])) > 0.0
####


def test_progress_is_bounded_by_available_unreacted_fraction() -> None:
    backend, state, config = _uniform_reactive_state(24)
    progress_rate = np.full(24, 1000.0, dtype=np.float64)

    updated = apply_reaction_source(
        state,
        progress_rate,
        force_density=None,
        timestep=1.0,
        config=config,
        backend=backend,
    )
    _density, _velocity, _pressure, progress = reactive_conservative_to_primitive(
        updated,
        config,
        backend,
    )

    assert np.allclose(progress, 1.0)
####
