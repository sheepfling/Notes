from __future__ import annotations

from dataclasses import dataclass

from converging_flow.backend import Array, ArrayBackend
from converging_flow.euler_backend import (
    advance_rusanov_backend,
    enforce_physical_state_backend,
)


@dataclass(frozen=True, slots=True)
class EulerSourceConfig:
    """Safe generic Euler-source coupling for combustion-like demonstrations.

    ``heat_release_per_mass`` converts reacted progress into specific internal
    energy. Pressure then follows from the Euler equation of state. A separate
    force density is accepted only for independently modeled momentum transfer;
    thermodynamic pressure itself already belongs in the Euler flux.
    """

    heat_release_per_mass: float
    gamma: float = 1.4
    density_floor: float = 1.0e-8
    pressure_floor: float = 1.0e-8

    def __post_init__(self) -> None:
        if self.heat_release_per_mass < 0.0:
            raise ValueError("heat_release_per_mass cannot be negative")
        ####
        if self.gamma <= 1.0:
            raise ValueError("gamma must be greater than one")
        ####
        if self.density_floor <= 0.0 or self.pressure_floor <= 0.0:
            raise ValueError("density and pressure floors must be positive")
        ####
    ####
####


def reaction_heat_release_rate_density(
    density: Array,
    progress_rate: Array,
    config: EulerSourceConfig,
    backend: ArrayBackend,
) -> Array:
    """Convert a nonnegative progress rate into volumetric heat-release rate."""
    bounded_rate = backend.xp.maximum(progress_rate, 0.0)
    return density * config.heat_release_per_mass * bounded_rate
####


def apply_euler_sources(
    state: Array,
    heat_release_rate_density: Array,
    force_density: Array | None,
    timestep: float,
    config: EulerSourceConfig,
    backend: ArrayBackend,
) -> Array:
    """Apply heat and optional force-density sources conservatively.

    Heat release is added to total energy. A genuine force density adds impulse
    to momentum, while its mechanical work is represented by the exact kinetic
    energy change over the source substep. Do not pass ``-grad(p)`` here: Euler
    pressure gradients are already present in the flux divergence.
    """
    if timestep <= 0.0:
        raise ValueError("timestep must be positive")
    ####

    updated = state.copy()
    dimensions = state.shape[0] - 2
    density = backend.xp.maximum(state[0], config.density_floor)
    old_momentum = state[1 : 1 + dimensions]

    if force_density is None:
        new_momentum = old_momentum
        kinetic_energy_change = backend.xp.zeros_like(density)
    else:
        expected_shape = (dimensions, *density.shape)
        if force_density.shape != expected_shape:
            raise ValueError(
                "force_density must have shape "
                f"{expected_shape}, got {force_density.shape}"
            )
        ####
        new_momentum = old_momentum + timestep * force_density
        old_kinetic = 0.5 * backend.xp.sum(
            old_momentum * old_momentum,
            axis=0,
        ) / density
        new_kinetic = 0.5 * backend.xp.sum(
            new_momentum * new_momentum,
            axis=0,
        ) / density
        kinetic_energy_change = new_kinetic - old_kinetic
        updated[1 : 1 + dimensions] = new_momentum
    ####

    updated[-1] += timestep * heat_release_rate_density + kinetic_energy_change
    return enforce_physical_state_backend(
        updated,
        config.gamma,
        config.density_floor,
        config.pressure_floor,
        backend,
    )
####


def advance_euler_with_sources(
    state: Array,
    heat_release_rate_density: Array,
    force_density: Array | None,
    timestep: float,
    spacing: tuple[float, ...],
    config: EulerSourceConfig,
    backend: ArrayBackend,
) -> Array:
    """Strang-split source/Euler/source step for prescribed source fields.

    Callers must choose a stable Euler timestep before invoking this low-level
    split step.
    """
    half_timestep = 0.5 * timestep
    half_source = apply_euler_sources(
        state,
        heat_release_rate_density,
        force_density,
        half_timestep,
        config,
        backend,
    )
    transported = advance_rusanov_backend(
        half_source,
        timestep,
        spacing,
        config.gamma,
        config.density_floor,
        config.pressure_floor,
        backend,
    )
    return apply_euler_sources(
        transported,
        heat_release_rate_density,
        force_density,
        half_timestep,
        config,
        backend,
    )
####
