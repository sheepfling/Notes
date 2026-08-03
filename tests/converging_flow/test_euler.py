from __future__ import annotations

import numpy as np
import pytest

from converging_flow.euler import (
    advance_rusanov,
    conservative_to_primitive,
    primitive_to_conservative,
    stable_timestep,
)


@pytest.mark.parametrize("dimensions", [1, 2, 3])
def test_uniform_state_is_stationary(dimensions: int) -> None:
    shape = (12,) * dimensions
    density = np.full(shape, 1.25)
    velocity = np.zeros((dimensions, *shape))
    pressure = np.full(shape, 0.8)
    state = primitive_to_conservative(density, velocity, pressure, gamma=1.4)
    spacing = (0.1,) * dimensions

    timestep = stable_timestep(
        state,
        spacing,
        gamma=1.4,
        cfl=0.35,
        density_floor=1.0e-8,
        pressure_floor=1.0e-8,
    )
    updated = advance_rusanov(
        state,
        timestep,
        spacing,
        gamma=1.4,
        density_floor=1.0e-8,
        pressure_floor=1.0e-8,
    )

    np.testing.assert_allclose(updated, state, rtol=0.0, atol=0.0)
####


def test_primitive_round_trip() -> None:
    density = np.linspace(0.8, 1.2, 32)
    velocity = np.stack((np.linspace(-0.2, 0.2, 32),))
    pressure = np.linspace(0.6, 1.4, 32)

    state = primitive_to_conservative(density, velocity, pressure, gamma=1.4)
    recovered_density, recovered_velocity, recovered_pressure = conservative_to_primitive(
        state,
        gamma=1.4,
        density_floor=1.0e-12,
        pressure_floor=1.0e-12,
    )

    np.testing.assert_allclose(recovered_density, density)
    np.testing.assert_allclose(recovered_velocity, velocity)
    np.testing.assert_allclose(recovered_pressure, pressure)
####
