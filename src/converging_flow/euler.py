from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


def primitive_to_conservative(
    density: FloatArray,
    velocity: FloatArray,
    pressure: FloatArray,
    gamma: float,
) -> FloatArray:
    """Convert primitive fields to conservative Euler variables."""
    if velocity.ndim != density.ndim + 1:
        raise ValueError("velocity must have shape (dimensions, *density.shape)")
    ####

    kinetic_density = 0.5 * density * np.sum(velocity * velocity, axis=0)
    total_energy = pressure / (gamma - 1.0) + kinetic_density
    return np.concatenate(
        (
            density[np.newaxis, ...],
            density[np.newaxis, ...] * velocity,
            total_energy[np.newaxis, ...],
        ),
        axis=0,
    )
####


def conservative_to_primitive(
    state: FloatArray,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Convert conservative fields to primitive variables with diagnostic floors."""
    dimensions = state.shape[0] - 2
    density = np.maximum(state[0], density_floor)
    velocity = state[1 : 1 + dimensions] / density[np.newaxis, ...]
    kinetic_density = 0.5 * density * np.sum(velocity * velocity, axis=0)
    pressure = np.maximum(
        (gamma - 1.0) * (state[-1] - kinetic_density),
        pressure_floor,
    )
    return density, velocity, pressure
####


def enforce_physical_state(
    state: FloatArray,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
) -> FloatArray:
    """Apply minimal positivity repair after an explicit update."""
    repaired = state.copy()
    dimensions = state.shape[0] - 2
    repaired[0] = np.maximum(repaired[0], density_floor)

    density = repaired[0]
    momentum = repaired[1 : 1 + dimensions]
    kinetic_density = 0.5 * np.sum(momentum * momentum, axis=0) / density
    minimum_energy = kinetic_density + pressure_floor / (gamma - 1.0)
    repaired[-1] = np.maximum(repaired[-1], minimum_energy)
    return repaired
####


def _physical_flux(
    state: FloatArray,
    axis: int,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
) -> FloatArray:
    density, velocity, pressure = conservative_to_primitive(
        state,
        gamma,
        density_floor,
        pressure_floor,
    )
    dimensions = velocity.shape[0]
    normal_velocity = velocity[axis]

    flux = np.empty_like(state)
    flux[0] = state[1 + axis]
    flux[1 : 1 + dimensions] = state[1 : 1 + dimensions] * normal_velocity
    flux[1 + axis] += pressure
    flux[-1] = (state[-1] + pressure) * normal_velocity
    return flux
####


def _interface_states(state: FloatArray, axis: int) -> tuple[FloatArray, FloatArray]:
    """Construct reflected wall ghost states along one spatial axis."""
    spatial_axis = axis + 1
    pad_width = [(0, 0)] * state.ndim
    pad_width[spatial_axis] = (1, 1)
    padded = np.pad(state, pad_width, mode="edge")

    lower_ghost = [slice(None)] * padded.ndim
    upper_ghost = [slice(None)] * padded.ndim
    lower_ghost[0] = 1 + axis
    upper_ghost[0] = 1 + axis
    lower_ghost[spatial_axis] = 0
    upper_ghost[spatial_axis] = -1
    padded[tuple(lower_ghost)] *= -1.0
    padded[tuple(upper_ghost)] *= -1.0

    left_slice = [slice(None)] * padded.ndim
    right_slice = [slice(None)] * padded.ndim
    left_slice[spatial_axis] = slice(0, state.shape[spatial_axis] + 1)
    right_slice[spatial_axis] = slice(1, state.shape[spatial_axis] + 2)
    return padded[tuple(left_slice)], padded[tuple(right_slice)]
####


def rusanov_interface_flux(
    state: FloatArray,
    axis: int,
    gamma: float,
    density_floor: float,
    pressure_floor: float,
) -> FloatArray:
    """Compute local Lax-Friedrichs/Rusanov fluxes at every interface."""
    left, right = _interface_states(state, axis)
    flux_left = _physical_flux(left, axis, gamma, density_floor, pressure_floor)
    flux_right = _physical_flux(right, axis, gamma, density_floor, pressure_floor)

    density_left, velocity_left, pressure_left = conservative_to_primitive(
        left,
        gamma,
        density_floor,
        pressure_floor,
    )
    density_right, velocity_right, pressure_right = conservative_to_primitive(
        right,
        gamma,
        density_floor,
        pressure_floor,
    )
    sound_left = np.sqrt(gamma * pressure_left / density_left)
    sound_right = np.sqrt(gamma * pressure_right / density_right)
    wave_speed = np.maximum(
        np.abs(velocity_left[axis]) + sound_left,
        np.abs(velocity_right[axis]) + sound_right,
    )

    return 0.5 * (flux_left + flux_right) - 0.5 * wave_speed * (right - left)
####


def stable_timestep(
    state: FloatArray,
    spacing: tuple[float, ...],
    gamma: float,
    cfl: float,
    density_floor: float,
    pressure_floor: float,
) -> float:
    """Return an unsplit multidimensional CFL timestep."""
    density, velocity, pressure = conservative_to_primitive(
        state,
        gamma,
        density_floor,
        pressure_floor,
    )
    sound_speed = np.sqrt(gamma * pressure / density)

    inverse_dt = 0.0
    for axis, dx in enumerate(spacing):
        inverse_dt += float(np.max(np.abs(velocity[axis]) + sound_speed)) / dx
    ####

    if inverse_dt <= 0.0:
        raise RuntimeError("non-positive CFL denominator")
    ####
    return cfl / inverse_dt
####


def advance_rusanov(
    state: FloatArray,
    timestep: float,
    spacing: tuple[float, ...],
    gamma: float,
    density_floor: float,
    pressure_floor: float,
) -> FloatArray:
    """Advance one first-order finite-volume Euler step."""
    dimensions = state.shape[0] - 2
    if dimensions != len(spacing):
        raise ValueError("state dimensions and spacing do not match")
    ####

    divergence = np.zeros_like(state)
    for axis, dx in enumerate(spacing):
        interface_flux = rusanov_interface_flux(
            state,
            axis,
            gamma,
            density_floor,
            pressure_floor,
        )
        divergence += np.diff(interface_flux, axis=axis + 1) / dx
    ####

    updated = state - timestep * divergence
    return enforce_physical_state(
        updated,
        gamma,
        density_floor,
        pressure_floor,
    )
####
