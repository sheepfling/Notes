from __future__ import annotations

import numpy as np
import pytest

from converging_flow.backend import get_array_backend
from converging_flow.euler_backend import (
    conservative_to_primitive_backend,
    primitive_to_conservative_backend,
)
from converging_flow.thermochemical import (
    EulerSourceConfig,
    apply_euler_sources,
    reaction_heat_release_rate_density,
)


def _uniform_state() -> tuple[object, object]:
    backend = get_array_backend("numpy")
    density = np.ones(32, dtype=np.float64)
    velocity = np.zeros((1, 32), dtype=np.float64)
    pressure = np.ones(32, dtype=np.float64)
    state = primitive_to_conservative_backend(
        density,
        velocity,
        pressure,
        1.4,
        backend,
    )
    return backend, state
####


def test_heat_release_raises_pressure_without_direct_momentum_source() -> None:
    backend, state = _uniform_state()
    config = EulerSourceConfig(heat_release_per_mass=2.0, gamma=1.4)
    progress_increment = np.full(32, 0.1, dtype=np.float64)
    heat_density = reaction_heat_release_rate_density(
        state[0],
        progress_increment,
        config,
        backend,
    )

    updated = apply_euler_sources(
        state,
        heat_density,
        force_density=None,
        timestep=1.0,
        config=config,
        backend=backend,
    )
    _density, velocity, pressure = conservative_to_primitive_backend(
        updated,
        config.gamma,
        config.density_floor,
        config.pressure_floor,
        backend,
    )

    assert np.allclose(velocity, 0.0)
    assert np.allclose(pressure, 1.0 + (config.gamma - 1.0) * 0.2)
####


def test_force_density_changes_momentum_and_accounts_for_work() -> None:
    backend, state = _uniform_state()
    config = EulerSourceConfig(heat_release_per_mass=0.0, gamma=1.4)
    heat_density = np.zeros(32, dtype=np.float64)
    force_density = np.full((1, 32), 0.5, dtype=np.float64)

    updated = apply_euler_sources(
        state,
        heat_density,
        force_density,
        timestep=0.2,
        config=config,
        backend=backend,
    )
    _density, velocity, pressure = conservative_to_primitive_backend(
        updated,
        config.gamma,
        config.density_floor,
        config.pressure_floor,
        backend,
    )

    assert np.allclose(velocity, 0.1)
    assert np.allclose(pressure, 1.0)
####


def test_force_density_shape_is_validated() -> None:
    backend, state = _uniform_state()
    config = EulerSourceConfig(heat_release_per_mass=0.0)

    with pytest.raises(ValueError, match="force_density must have shape"):
        apply_euler_sources(
            state,
            np.zeros(32, dtype=np.float64),
            np.zeros((2, 32), dtype=np.float64),
            timestep=0.1,
            config=config,
            backend=backend,
        )
    ####
####
