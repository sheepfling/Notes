from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from converging_flow.backend import Array, ArrayBackend


@dataclass(frozen=True, slots=True)
class ReactiveEulerConfig:
    """Generic calorically perfect reactive-gas configuration.

    ``progress`` is a bounded mass-specific reaction coordinate from zero to
    one. ``heat_release_per_mass`` is normalized specific energy released as
    progress advances by one. No particular chemistry or energetic material is
    implied.
    """

    gamma: float = 1.4
    gas_constant: float = 1.0
    specific_heat: float = 2.5
    heat_release_per_mass: float = 1.0
    density_floor: float = 1.0e-8
    pressure_floor: float = 1.0e-8

    def __post_init__(self) -> None:
        if self.gamma <= 1.0:
            raise ValueError("gamma must be greater than one")
        ####
        if self.gas_constant <= 0.0 or self.specific_heat <= 0.0:
            raise ValueError("gas_constant and specific_heat must be positive")
        ####
        if not np.isclose(
            self.gamma,
            1.0 + self.gas_constant / self.specific_heat,
            rtol=1.0e-12,
            atol=1.0e-12,
        ):
            raise ValueError("gamma must equal 1 + gas_constant / specific_heat")
        ####
        if self.heat_release_per_mass < 0.0:
            raise ValueError("heat_release_per_mass cannot be negative")
        ####
        if self.density_floor <= 0.0 or self.pressure_floor <= 0.0:
            raise ValueError("density and pressure floors must be positive")
        ####
    ####
####


def primitive_to_reactive_conservative(
    density: Array,
    velocity: Array,
    pressure: Array,
    progress: Array,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> Array:
    if velocity.ndim != density.ndim + 1:
        raise ValueError("velocity must have shape (dimensions, *density.shape)")
    ####
    if progress.shape != density.shape:
        raise ValueError("progress and density must have identical shapes")
    ####

    bounded_progress = backend.xp.clip(progress, 0.0, 1.0)
    kinetic_density = 0.5 * density * backend.xp.sum(
        velocity * velocity,
        axis=0,
    )
    total_energy = pressure / (config.gamma - 1.0) + kinetic_density
    return backend.xp.concatenate(
        (
            density[None, ...],
            density[None, ...] * velocity,
            total_energy[None, ...],
            (density * bounded_progress)[None, ...],
        ),
        axis=0,
    )
####


def reactive_conservative_to_primitive(
    state: Array,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> tuple[Array, Array, Array, Array]:
    dimensions = state.shape[0] - 3
    if dimensions not in (1, 2, 3):
        raise ValueError("reactive state must represent one, two, or three dimensions")
    ####

    density = backend.xp.maximum(state[0], config.density_floor)
    momentum = state[1 : 1 + dimensions]
    velocity = momentum / density[None, ...]
    kinetic_density = 0.5 * backend.xp.sum(
        momentum * momentum,
        axis=0,
    ) / density
    pressure = backend.xp.maximum(
        (config.gamma - 1.0) * (state[-2] - kinetic_density),
        config.pressure_floor,
    )
    progress = backend.xp.clip(state[-1] / density, 0.0, 1.0)
    return density, velocity, pressure, progress
####


def enforce_reactive_physical_state(
    state: Array,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> Array:
    repaired = state.copy()
    dimensions = state.shape[0] - 3
    repaired[0] = backend.xp.maximum(repaired[0], config.density_floor)
    density = repaired[0]
    momentum = repaired[1 : 1 + dimensions]
    kinetic_density = 0.5 * backend.xp.sum(
        momentum * momentum,
        axis=0,
    ) / density
    minimum_energy = kinetic_density + config.pressure_floor / (
        config.gamma - 1.0
    )
    repaired[-2] = backend.xp.maximum(repaired[-2], minimum_energy)
    repaired[-1] = backend.xp.clip(repaired[-1], 0.0, density)
    return repaired
####


def _physical_flux(
    state: Array,
    axis: int,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> Array:
    _density, velocity, pressure, _progress = (
        reactive_conservative_to_primitive(state, config, backend)
    )
    dimensions = velocity.shape[0]
    normal_velocity = velocity[axis]

    flux = backend.xp.empty_like(state)
    flux[0] = state[1 + axis]
    flux[1 : 1 + dimensions] = (
        state[1 : 1 + dimensions] * normal_velocity
    )
    flux[1 + axis] += pressure
    flux[-2] = (state[-2] + pressure) * normal_velocity
    flux[-1] = state[-1] * normal_velocity
    return flux
####


def _interface_states(
    state: Array,
    axis: int,
    backend: ArrayBackend,
) -> tuple[Array, Array]:
    spatial_axis = axis + 1
    pad_width = [(0, 0)] * state.ndim
    pad_width[spatial_axis] = (1, 1)
    padded = backend.xp.pad(state, pad_width, mode="edge")

    lower_ghost: list[Any] = [slice(None)] * padded.ndim
    upper_ghost: list[Any] = [slice(None)] * padded.ndim
    lower_ghost[0] = 1 + axis
    upper_ghost[0] = 1 + axis
    lower_ghost[spatial_axis] = 0
    upper_ghost[spatial_axis] = -1
    padded[tuple(lower_ghost)] *= -1.0
    padded[tuple(upper_ghost)] *= -1.0

    left_slice: list[Any] = [slice(None)] * padded.ndim
    right_slice: list[Any] = [slice(None)] * padded.ndim
    left_slice[spatial_axis] = slice(0, state.shape[spatial_axis] + 1)
    right_slice[spatial_axis] = slice(1, state.shape[spatial_axis] + 2)
    return padded[tuple(left_slice)], padded[tuple(right_slice)]
####


def rusanov_interface_flux(
    state: Array,
    axis: int,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> Array:
    left, right = _interface_states(state, axis, backend)
    flux_left = _physical_flux(left, axis, config, backend)
    flux_right = _physical_flux(right, axis, config, backend)

    density_left, velocity_left, pressure_left, _progress_left = (
        reactive_conservative_to_primitive(left, config, backend)
    )
    density_right, velocity_right, pressure_right, _progress_right = (
        reactive_conservative_to_primitive(right, config, backend)
    )
    sound_left = backend.xp.sqrt(
        config.gamma * pressure_left / density_left
    )
    sound_right = backend.xp.sqrt(
        config.gamma * pressure_right / density_right
    )
    wave_speed = backend.xp.maximum(
        backend.xp.abs(velocity_left[axis]) + sound_left,
        backend.xp.abs(velocity_right[axis]) + sound_right,
    )
    return 0.5 * (flux_left + flux_right) - 0.5 * wave_speed * (
        right - left
    )
####


def stable_reactive_timestep(
    state: Array,
    spacing: tuple[float, ...],
    cfl: float,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> float:
    density, velocity, pressure, _progress = (
        reactive_conservative_to_primitive(state, config, backend)
    )
    sound_speed = backend.xp.sqrt(config.gamma * pressure / density)
    inverse_timestep = 0.0
    for axis, delta in enumerate(spacing):
        maximum_speed = backend.scalar(
            backend.xp.max(backend.xp.abs(velocity[axis]) + sound_speed)
        )
        inverse_timestep += maximum_speed / delta
    ####
    if inverse_timestep <= 0.0:
        raise RuntimeError("non-positive CFL denominator")
    ####
    return cfl / inverse_timestep
####


def advance_reactive_rusanov(
    state: Array,
    timestep: float,
    spacing: tuple[float, ...],
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> Array:
    dimensions = state.shape[0] - 3
    if dimensions != len(spacing):
        raise ValueError("state dimensions and spacing do not match")
    ####

    divergence = backend.xp.zeros_like(state)
    for axis, delta in enumerate(spacing):
        interface_flux = rusanov_interface_flux(
            state,
            axis,
            config,
            backend,
        )
        divergence += backend.xp.diff(
            interface_flux,
            axis=axis + 1,
        ) / delta
    ####
    return enforce_reactive_physical_state(
        state - timestep * divergence,
        config,
        backend,
    )
####


def apply_reaction_source(
    state: Array,
    progress_rate: Array,
    force_density: Array | None,
    timestep: float,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> Array:
    """Advance progress and release heat into Euler total energy.

    ``progress_rate`` has units of progress per time following the material.
    Pressure is not inserted as a body force: released energy changes the EOS
    pressure, whose gradient acts through the subsequent Euler flux step.
    """
    if timestep <= 0.0:
        raise ValueError("timestep must be positive")
    ####

    updated = state.copy()
    dimensions = state.shape[0] - 3
    density, _velocity, _pressure, progress = (
        reactive_conservative_to_primitive(state, config, backend)
    )
    available_progress = backend.xp.maximum(1.0 - progress, 0.0)
    progress_increment = backend.xp.minimum(
        timestep * backend.xp.maximum(progress_rate, 0.0),
        available_progress,
    )
    updated[-1] += density * progress_increment
    updated[-2] += (
        density * config.heat_release_per_mass * progress_increment
    )

    if force_density is not None:
        expected_shape = (dimensions, *density.shape)
        if force_density.shape != expected_shape:
            raise ValueError(
                "force_density must have shape "
                f"{expected_shape}, got {force_density.shape}"
            )
        ####
        old_momentum = state[1 : 1 + dimensions]
        new_momentum = old_momentum + timestep * force_density
        old_kinetic = 0.5 * backend.xp.sum(
            old_momentum * old_momentum,
            axis=0,
        ) / density
        new_kinetic = 0.5 * backend.xp.sum(
            new_momentum * new_momentum,
            axis=0,
        ) / density
        updated[1 : 1 + dimensions] = new_momentum
        updated[-2] += new_kinetic - old_kinetic
    ####

    return enforce_reactive_physical_state(updated, config, backend)
####


def advance_reactive_euler_split(
    state: Array,
    progress_rate: Array,
    force_density: Array | None,
    timestep: float,
    spacing: tuple[float, ...],
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> Array:
    """Second-order source/transport/source update for prescribed rates."""
    half_timestep = 0.5 * timestep
    sourced = apply_reaction_source(
        state,
        progress_rate,
        force_density,
        half_timestep,
        config,
        backend,
    )
    transported = advance_reactive_rusanov(
        sourced,
        timestep,
        spacing,
        config,
        backend,
    )
    return apply_reaction_source(
        transported,
        progress_rate,
        force_density,
        half_timestep,
        config,
        backend,
    )
####
