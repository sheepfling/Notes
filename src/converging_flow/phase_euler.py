"""Normalized impulsive-source Euler flow with an irreversible phase fraction.

This module intentionally models a generic calorically-perfect continuum.  The
phase fraction is a numerically convenient state variable, not a calibrated
equation of state for a named material.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from converging_flow.backend import Array, ArrayBackend

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class PhaseEulerConfig:
    """Dimensionless coefficients for a finite impulsive energy source.

    ``activity`` consumes a finite unit reservoir and releases
    ``heat_release_per_mass`` as it advances.  ``phase_fraction`` is an
    irreversible 0-to-1 transition that consumes ``latent_heat_per_mass``.
    Temperature is the ideal-gas diagnostic ``pressure / (density * R)``.
    """

    gamma: float = 1.4
    gas_constant: float = 1.0
    specific_heat: float = 2.5
    heat_release_per_mass: float = 6.0
    activity_growth_rate: float = 75.0
    latent_heat_per_mass: float = 1.0
    transition_temperature: float = 2.0
    transition_width: float = 0.08
    phase_relaxation_time: float = 0.012
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
        if self.activity_growth_rate < 0.0:
            raise ValueError("activity_growth_rate cannot be negative")
        ####
        if self.latent_heat_per_mass < 0.0:
            raise ValueError("latent_heat_per_mass cannot be negative")
        ####
        if self.transition_width <= 0.0:
            raise ValueError("transition_width must be positive")
        ####
        if self.phase_relaxation_time <= 0.0:
            raise ValueError("phase_relaxation_time must be positive")
        ####
        if self.density_floor <= 0.0 or self.pressure_floor <= 0.0:
            raise ValueError("density and pressure floors must be positive")
        ####
    ####
####


@dataclass(frozen=True, slots=True)
class ImpulsiveEventValidation:
    """Outcome checks for a captured generic impulsive-event history."""

    source_activation_time: float | None
    pressure_wave_time: float | None
    phase_onset_time: float | None
    maximum_pressure_rise: float
    maximum_phase_fraction: float
    minimum_velocity: float
    maximum_velocity: float
    energy_residual: float
    energy_tolerance: float
    bounded_fractions: bool
    finite_fields: bool
    source_activates: bool
    pressure_wave_forms: bool
    phase_transition_occurs: bool
    outward_motion_forms: bool
    causal_order: bool
    energy_closes: bool

    @property
    def passed(self) -> bool:
        return all(
            (
                self.bounded_fractions,
                self.finite_fields,
                self.source_activates,
                self.pressure_wave_forms,
                self.phase_transition_occurs,
                self.outward_motion_forms,
                self.causal_order,
                self.energy_closes,
            )
        )
    ####
####


def _first_threshold_time(
    times: FloatArray,
    values: FloatArray,
    threshold: float,
) -> float | None:
    indices = np.flatnonzero(values >= threshold)
    if indices.size == 0:
        return None
    ####
    return float(times[int(indices[0])])
####


def validate_impulsive_event_history(
    coordinate: FloatArray,
    times: FloatArray,
    density_history: FloatArray,
    velocity_history: FloatArray,
    pressure_history: FloatArray,
    activity_history: FloatArray,
    phase_history: FloatArray,
    config: PhaseEulerConfig,
) -> ImpulsiveEventValidation:
    """Check the expected finite-source → pressure → phase-event sequence.

    This intentionally validates qualitative milestones and conservation rather
    than exact profile values, so it remains useful across CPU and GPU grids.
    """
    expected_shape = (times.size, coordinate.size)
    histories = (
        density_history,
        velocity_history,
        pressure_history,
        activity_history,
        phase_history,
    )
    if any(history.shape != expected_shape for history in histories):
        raise ValueError("all histories must have shape (frame_count, resolution)")
    ####
    if coordinate.size < 2:
        raise ValueError("at least two spatial cells are required")
    ####

    spacing = float(coordinate[1] - coordinate[0])
    activity_mass = np.sum(density_history * activity_history, axis=1) * spacing
    released_energy = config.heat_release_per_mass * (activity_mass - activity_mass[0])
    internal_energy = np.sum(pressure_history / (config.gamma - 1.0), axis=1) * spacing
    kinetic_energy = (
        np.sum(
            0.5 * density_history * velocity_history * velocity_history,
            axis=1,
        )
        * spacing
    )
    latent_energy = (
        config.latent_heat_per_mass
        * np.sum(density_history * phase_history, axis=1)
        * spacing
    )
    total_energy = internal_energy + kinetic_energy + latent_energy
    residual_history = total_energy - total_energy[0] - released_energy
    energy_residual = float(np.max(np.abs(residual_history)))
    energy_tolerance = 1.0e-8 * max(1.0, float(np.max(np.abs(released_energy))))

    pressure_rise = np.max(pressure_history, axis=1) - float(
        np.max(pressure_history[0])
    )
    maximum_pressure_rise = float(np.max(pressure_rise))
    maximum_phase_fraction = float(np.max(phase_history))
    source_final = float(released_energy[-1])
    source_activation_time = (
        _first_threshold_time(times, released_energy, 0.01 * source_final)
        if source_final > 0.0
        else None
    )
    pressure_wave_time = _first_threshold_time(
        times,
        pressure_rise,
        max(0.05 * maximum_pressure_rise, 1.0e-6),
    )
    phase_onset_time = _first_threshold_time(times, np.max(phase_history, axis=1), 0.10)
    minimum_velocity = float(np.min(velocity_history))
    maximum_velocity = float(np.max(velocity_history))
    source_activates = source_final > 0.0 and float(np.max(activity_history)) > 0.50
    pressure_wave_forms = maximum_pressure_rise > 0.10
    phase_transition_occurs = maximum_phase_fraction > 0.50
    outward_motion_forms = minimum_velocity < -0.05 and maximum_velocity > 0.05
    causal_order = (
        source_activation_time is not None
        and pressure_wave_time is not None
        and phase_onset_time is not None
        and source_activation_time <= pressure_wave_time <= phase_onset_time
    )
    bounded_fractions = bool(
        np.all((activity_history >= 0.0) & (activity_history <= 1.0))
        and np.all((phase_history >= 0.0) & (phase_history <= 1.0))
    )
    finite_fields = bool(all(np.all(np.isfinite(history)) for history in histories))
    return ImpulsiveEventValidation(
        source_activation_time=source_activation_time,
        pressure_wave_time=pressure_wave_time,
        phase_onset_time=phase_onset_time,
        maximum_pressure_rise=maximum_pressure_rise,
        maximum_phase_fraction=maximum_phase_fraction,
        minimum_velocity=minimum_velocity,
        maximum_velocity=maximum_velocity,
        energy_residual=energy_residual,
        energy_tolerance=energy_tolerance,
        bounded_fractions=bounded_fractions,
        finite_fields=finite_fields,
        source_activates=source_activates,
        pressure_wave_forms=pressure_wave_forms,
        phase_transition_occurs=phase_transition_occurs,
        outward_motion_forms=outward_motion_forms,
        causal_order=causal_order,
        energy_closes=energy_residual <= energy_tolerance,
    )
####


def primitive_to_phase_conservative(
    density: Array,
    velocity: Array,
    pressure: Array,
    activity: Array,
    phase_fraction: Array,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    """Pack primitive fields as ``[rho, rho*u..., E, rho*a, rho*phi]``."""
    if velocity.ndim != density.ndim + 1:
        raise ValueError("velocity must have shape (dimensions, *density.shape)")
    ####
    if (
        pressure.shape != density.shape
        or activity.shape != density.shape
        or phase_fraction.shape != density.shape
    ):
        raise ValueError("all scalar fields must have the density shape")
    ####

    bounded_activity = backend.xp.clip(activity, 0.0, 1.0)
    bounded_phase = backend.xp.clip(phase_fraction, 0.0, 1.0)
    kinetic_density = 0.5 * density * backend.xp.sum(velocity * velocity, axis=0)
    total_energy = pressure / (config.gamma - 1.0) + kinetic_density
    return backend.xp.concatenate(
        (
            density[None, ...],
            density[None, ...] * velocity,
            total_energy[None, ...],
            (density * bounded_activity)[None, ...],
            (density * bounded_phase)[None, ...],
        ),
        axis=0,
    )
####


def phase_conservative_to_primitive(
    state: Array,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> tuple[Array, Array, Array, Array, Array]:
    """Unpack density, velocity, EOS pressure, activity, and phase fraction."""
    dimensions = state.shape[0] - 4
    if dimensions not in (1, 2, 3):
        raise ValueError("phase state must represent one, two, or three dimensions")
    ####
    density = backend.xp.maximum(state[0], config.density_floor)
    momentum = state[1 : 1 + dimensions]
    velocity = momentum / density[None, ...]
    kinetic_density = 0.5 * backend.xp.sum(momentum * momentum, axis=0) / density
    pressure = backend.xp.maximum(
        (config.gamma - 1.0) * (state[-3] - kinetic_density),
        config.pressure_floor,
    )
    activity = backend.xp.clip(state[-2] / density, 0.0, 1.0)
    phase_fraction = backend.xp.clip(state[-1] / density, 0.0, 1.0)
    return density, velocity, pressure, activity, phase_fraction
####


def enforce_phase_physical_state(
    state: Array,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    """Apply positivity floors and bound the two material-fraction scalars."""
    repaired = state.copy()
    dimensions = state.shape[0] - 4
    repaired[0] = backend.xp.maximum(repaired[0], config.density_floor)
    density = repaired[0]
    momentum = repaired[1 : 1 + dimensions]
    kinetic_density = 0.5 * backend.xp.sum(momentum * momentum, axis=0) / density
    minimum_energy = kinetic_density + config.pressure_floor / (config.gamma - 1.0)
    repaired[-3] = backend.xp.maximum(repaired[-3], minimum_energy)
    repaired[-2] = backend.xp.clip(repaired[-2], 0.0, density)
    repaired[-1] = backend.xp.clip(repaired[-1], 0.0, density)
    return repaired
####


def _physical_flux(
    state: Array,
    axis: int,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    _density, velocity, pressure, _activity, _phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
    )
    dimensions = velocity.shape[0]
    normal_velocity = velocity[axis]
    flux = backend.xp.empty_like(state)
    flux[0] = state[1 + axis]
    flux[1 : 1 + dimensions] = state[1 : 1 + dimensions] * normal_velocity
    flux[1 + axis] += pressure
    flux[-3] = (state[-3] + pressure) * normal_velocity
    flux[-2] = state[-2] * normal_velocity
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


def phase_rusanov_interface_flux(
    state: Array,
    axis: int,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    left, right = _interface_states(state, axis, backend)
    flux_left = _physical_flux(left, axis, config, backend)
    flux_right = _physical_flux(right, axis, config, backend)
    density_left, velocity_left, pressure_left, _activity_left, _phase_left = (
        phase_conservative_to_primitive(left, config, backend)
    )
    density_right, velocity_right, pressure_right, _activity_right, _phase_right = (
        phase_conservative_to_primitive(right, config, backend)
    )
    sound_left = backend.xp.sqrt(config.gamma * pressure_left / density_left)
    sound_right = backend.xp.sqrt(config.gamma * pressure_right / density_right)
    wave_speed = backend.xp.maximum(
        backend.xp.abs(velocity_left[axis]) + sound_left,
        backend.xp.abs(velocity_right[axis]) + sound_right,
    )
    return 0.5 * (flux_left + flux_right) - 0.5 * wave_speed * (right - left)
####


def stable_phase_timestep(
    state: Array,
    spacing: tuple[float, ...],
    cfl: float,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> float:
    density, velocity, pressure, _activity, _phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
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


def advance_phase_rusanov(
    state: Array,
    timestep: float,
    spacing: tuple[float, ...],
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    dimensions = state.shape[0] - 4
    if dimensions != len(spacing):
        raise ValueError("state dimensions and spacing do not match")
    ####
    divergence = backend.xp.zeros_like(state)
    for axis, delta in enumerate(spacing):
        interface_flux = phase_rusanov_interface_flux(state, axis, config, backend)
        divergence += backend.xp.diff(interface_flux, axis=axis + 1) / delta
    ####
    return enforce_phase_physical_state(state - timestep * divergence, config, backend)
####


def phase_equilibrium_fraction(
    temperature: Array,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    """Return a smooth temperature-threshold target phase fraction."""
    argument = backend.xp.clip(
        (temperature - config.transition_temperature) / config.transition_width,
        -60.0,
        60.0,
    )
    return 1.0 / (1.0 + backend.xp.exp(-argument))
####


def apply_impulsive_source(
    state: Array,
    source_profile: Array,
    timestep: float,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    """Advance finite feedback-driven activity and irreversible phase change.

    The activity source is local and logistic, so it grows rapidly from a seed
    but can release only a finite configured energy reservoir.  The phase
    update removes latent heat from Euler internal energy; the ensuing pressure
    response is generated by the EOS and conservative transport step.
    """
    if timestep <= 0.0:
        raise ValueError("timestep must be positive")
    ####
    if source_profile.shape != state.shape[1:]:
        raise ValueError("source_profile must match the spatial state shape")
    ####

    updated = state.copy()
    density, _velocity, _pressure, activity, _phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
    )
    activity_rate = (
        config.activity_growth_rate
        * backend.xp.maximum(source_profile, 0.0)
        * activity
        * backend.xp.maximum(1.0 - activity, 0.0)
    )
    activity_increment = backend.xp.minimum(
        timestep * activity_rate,
        backend.xp.maximum(1.0 - activity, 0.0),
    )
    updated[-2] += density * activity_increment
    updated[-3] += density * config.heat_release_per_mass * activity_increment

    (
        updated_density,
        updated_velocity,
        updated_pressure,
        _updated_activity,
        updated_phase,
    ) = phase_conservative_to_primitive(updated, config, backend)
    del updated_velocity
    temperature = updated_pressure / (updated_density * config.gas_constant)
    phase_target = phase_equilibrium_fraction(temperature, config, backend)
    desired_phase_increment = (
        timestep
        * backend.xp.maximum(phase_target - updated_phase, 0.0)
        / config.phase_relaxation_time
    )
    if config.latent_heat_per_mass > 0.0:
        internal_energy = (
            updated[-3]
            - 0.5
            * backend.xp.sum(updated[1:-3] * updated[1:-3], axis=0)
            / updated_density
        )
        minimum_internal = config.pressure_floor / (config.gamma - 1.0)
        latent_limited_increment = backend.xp.maximum(
            internal_energy - minimum_internal,
            0.0,
        ) / (updated_density * config.latent_heat_per_mass)
        phase_increment = backend.xp.minimum(
            desired_phase_increment,
            latent_limited_increment,
        )
    else:
        phase_increment = desired_phase_increment
    ####
    phase_increment = backend.xp.minimum(
        phase_increment,
        backend.xp.maximum(1.0 - updated_phase, 0.0),
    )
    updated[-1] += updated_density * phase_increment
    updated[-3] -= updated_density * config.latent_heat_per_mass * phase_increment
    return enforce_phase_physical_state(updated, config, backend)
####


def advance_impulsive_phase_euler_split(
    state: Array,
    source_profile: Array,
    timestep: float,
    spacing: tuple[float, ...],
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> Array:
    """Second-order source/transport/source update for the generic event."""
    half_timestep = 0.5 * timestep
    sourced = apply_impulsive_source(
        state,
        source_profile,
        half_timestep,
        config,
        backend,
    )
    transported = advance_phase_rusanov(
        sourced,
        timestep,
        spacing,
        config,
        backend,
    )
    return apply_impulsive_source(
        transported,
        source_profile,
        half_timestep,
        config,
        backend,
    )
####
