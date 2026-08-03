from __future__ import annotations

from typing import Any

from converging_flow.backend import Array, ArrayBackend


def primitive_to_conservative_backend(
    density: Array,
    velocity: Array,
    pressure: Array,
    gamma: float,
    backend: ArrayBackend,
) -> Array:
    if velocity.ndim != density.ndim + 1:
        raise ValueError("velocity must have shape (dimensions, *density.shape)")
    ####

    kinetic_density = 0.5 * density * backend.xp.sum(
        velocity * velocity,
        axis=0,
    )
    total_energy = pressure / (gamma - 1.0) + kinetic_density
    return backend.xp.concatenate(
        (
            density[None, ...],
            density[None, ...] * velocity,
            total_energy[None, ...],
        ),
        axis=0,
    )
####


def conservative_to_primitive_backend(
    state: Array,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
    backend: ArrayBackend,
) -> tuple[Array, Array, Array]:
    dimensions = state.shape[0] - 2
    density = backend.xp.maximum(state[0], density_floor)
    velocity = state[1 : 1 + dimensions] / density[None, ...]
    kinetic_density = 0.5 * density * backend.xp.sum(
        velocity * velocity,
        axis=0,
    )
    pressure = backend.xp.maximum(
        (gamma - 1.0) * (state[-1] - kinetic_density),
        pressure_floor,
    )
    return density, velocity, pressure
####


def enforce_physical_state_backend(
    state: Array,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
    backend: ArrayBackend,
) -> Array:
    repaired = state.copy()
    dimensions = state.shape[0] - 2
    repaired[0] = backend.xp.maximum(repaired[0], density_floor)

    density = repaired[0]
    momentum = repaired[1 : 1 + dimensions]
    kinetic_density = 0.5 * backend.xp.sum(
        momentum * momentum,
        axis=0,
    ) / density
    minimum_energy = kinetic_density + pressure_floor / (gamma - 1.0)
    repaired[-1] = backend.xp.maximum(repaired[-1], minimum_energy)
    return repaired
####


def _physical_flux_backend(
    state: Array,
    axis: int,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
    backend: ArrayBackend,
) -> Array:
    _density, velocity, pressure = conservative_to_primitive_backend(
        state,
        gamma,
        density_floor,
        pressure_floor,
        backend,
    )
    dimensions = velocity.shape[0]
    normal_velocity = velocity[axis]

    flux = backend.xp.empty_like(state)
    flux[0] = state[1 + axis]
    flux[1 : 1 + dimensions] = (
        state[1 : 1 + dimensions] * normal_velocity
    )
    flux[1 + axis] += pressure
    flux[-1] = (state[-1] + pressure) * normal_velocity
    return flux
####


def _interface_states_backend(
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


def rusanov_interface_flux_backend(
    state: Array,
    axis: int,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
    backend: ArrayBackend,
) -> Array:
    left, right = _interface_states_backend(state, axis, backend)
    flux_left = _physical_flux_backend(
        left,
        axis,
        gamma,
        density_floor,
        pressure_floor,
        backend,
    )
    flux_right = _physical_flux_backend(
        right,
        axis,
        gamma,
        density_floor,
        pressure_floor,
        backend,
    )

    density_left, velocity_left, pressure_left = (
        conservative_to_primitive_backend(
            left,
            gamma,
            density_floor,
            pressure_floor,
            backend,
        )
    )
    density_right, velocity_right, pressure_right = (
        conservative_to_primitive_backend(
            right,
            gamma,
            density_floor,
            pressure_floor,
            backend,
        )
    )
    sound_left = backend.xp.sqrt(gamma * pressure_left / density_left)
    sound_right = backend.xp.sqrt(gamma * pressure_right / density_right)
    wave_speed = backend.xp.maximum(
        backend.xp.abs(velocity_left[axis]) + sound_left,
        backend.xp.abs(velocity_right[axis]) + sound_right,
    )

    return 0.5 * (flux_left + flux_right) - 0.5 * wave_speed * (
        right - left
    )
####


def stable_timestep_backend(
    state: Array,
    spacing: tuple[float, ...],
    gamma: float,
    cfl: float,
    density_floor: float,
    pressure_floor: float,
    backend: ArrayBackend,
) -> float:
    density, velocity, pressure = conservative_to_primitive_backend(
        state,
        gamma,
        density_floor,
        pressure_floor,
        backend,
    )
    sound_speed = backend.xp.sqrt(gamma * pressure / density)

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


def advance_rusanov_backend(
    state: Array,
    timestep: float,
    spacing: tuple[float, ...],
    gamma: float,
    density_floor: float,
    pressure_floor: float,
    backend: ArrayBackend,
) -> Array:
    dimensions = state.shape[0] - 2
    if dimensions != len(spacing):
        raise ValueError("state dimensions and spacing do not match")
    ####

    divergence = backend.xp.zeros_like(state)
    for axis, delta in enumerate(spacing):
        interface_flux = rusanov_interface_flux_backend(
            state,
            axis,
            gamma,
            density_floor,
            pressure_floor,
            backend,
        )
        divergence += backend.xp.diff(
            interface_flux,
            axis=axis + 1,
        ) / delta
    ####

    updated = state - timestep * divergence
    return enforce_physical_state_backend(
        updated,
        gamma,
        density_floor,
        pressure_floor,
        backend,
    )
####
