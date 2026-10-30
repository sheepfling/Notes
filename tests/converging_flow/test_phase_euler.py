from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from converging_flow.backend import Array, ArrayBackend, get_array_backend
from converging_flow.phase_euler import (
    PhaseEulerConfig,
    advance_impulsive_phase_euler_split,
    apply_impulsive_source,
    phase_conservative_to_primitive,
    primitive_to_phase_conservative,
    stable_phase_timestep,
    validate_impulsive_event_history,
)

FloatArray = NDArray[np.float64]


def _uniform_phase_state(
    size: int = 96,
    pressure_value: float = 1.0,
) -> tuple[ArrayBackend, Array, PhaseEulerConfig]:
    backend = get_array_backend("numpy")
    config = PhaseEulerConfig(
        heat_release_per_mass=4.0,
        activity_growth_rate=20.0,
        latent_heat_per_mass=0.8,
        transition_temperature=1.5,
        transition_width=0.05,
        phase_relaxation_time=0.01,
    )
    density = np.ones(size, dtype=np.float64)
    velocity = np.zeros((1, size), dtype=np.float64)
    pressure = np.full(size, pressure_value, dtype=np.float64)
    activity = np.full(size, 0.1, dtype=np.float64)
    phase_fraction = np.zeros(size, dtype=np.float64)
    state = primitive_to_phase_conservative(
        density,
        velocity,
        pressure,
        activity,
        phase_fraction,
        config,
        backend,
    )
    return backend, state, config
####


def test_finite_feedback_source_raises_pressure_and_activity() -> None:
    backend, state, config = _uniform_phase_state(32)
    source = np.ones(32, dtype=np.float64)

    updated = apply_impulsive_source(
        state,
        source,
        timestep=0.01,
        config=config,
        backend=backend,
    )
    _density, _velocity, pressure, activity, phase_fraction = (
        phase_conservative_to_primitive(updated, config, backend)
    )

    assert np.all(activity > 0.1)
    assert np.all(activity < 1.0)
    assert np.all(pressure > 1.0)
    assert float(np.max(phase_fraction)) < 1.0e-3
####


def test_hot_material_transforms_and_consumes_latent_energy() -> None:
    backend, state, config = _uniform_phase_state(32, pressure_value=3.0)
    source = np.zeros(32, dtype=np.float64)
    _density, _velocity, initial_pressure, _activity, _phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
    )

    updated = apply_impulsive_source(
        state,
        source,
        timestep=0.01,
        config=config,
        backend=backend,
    )
    _density, _velocity, pressure, _activity, phase_fraction = (
        phase_conservative_to_primitive(updated, config, backend)
    )

    assert np.all(phase_fraction > 0.0)
    assert np.all(phase_fraction <= 1.0)
    assert np.all(pressure < initial_pressure)
####


def test_localized_event_creates_outward_pressure_driven_motion() -> None:
    backend, state, config = _uniform_phase_state(128)
    coordinate = np.linspace(-1.0, 1.0, 128, dtype=np.float64)
    source = np.exp(-80.0 * coordinate * coordinate)

    updated = advance_impulsive_phase_euler_split(
        state,
        source,
        timestep=2.0e-3,
        spacing=(coordinate[1] - coordinate[0],),
        config=config,
        backend=backend,
    )
    _density, velocity, pressure, activity, _phase_fraction = (
        phase_conservative_to_primitive(updated, config, backend)
    )

    midpoint = coordinate.size // 2
    assert float(np.max(pressure)) > 1.0
    assert float(np.max(activity)) > 0.1
    assert float(np.min(velocity[0, :midpoint])) < 0.0
    assert float(np.max(velocity[0, midpoint:])) > 0.0
####


def test_impulsive_event_history_meets_expected_sequence() -> None:
    backend = get_array_backend("numpy")
    config = PhaseEulerConfig(
        heat_release_per_mass=6.0,
        activity_growth_rate=75.0,
        latent_heat_per_mass=1.0,
        transition_temperature=2.0,
        transition_width=0.08,
        phase_relaxation_time=0.012,
    )
    resolution = 96
    coordinate = np.linspace(-1.0, 1.0, resolution, dtype=np.float64)
    spacing = (float(coordinate[1] - coordinate[0]),)
    source = np.exp(-0.5 * (coordinate / 0.13) ** 2)
    density = np.ones(resolution, dtype=np.float64)
    velocity = np.zeros((1, resolution), dtype=np.float64)
    pressure = np.ones(resolution, dtype=np.float64)
    activity = 0.015 * source
    phase_fraction = np.zeros(resolution, dtype=np.float64)
    state = primitive_to_phase_conservative(
        density,
        velocity,
        pressure,
        activity,
        phase_fraction,
        config,
        backend,
    )

    times: list[float] = []
    density_history: list[FloatArray] = []
    velocity_history: list[FloatArray] = []
    pressure_history: list[FloatArray] = []
    activity_history: list[FloatArray] = []
    phase_history: list[FloatArray] = []
    time = 0.0
    final_time = 0.14
    while True:
        observed = phase_conservative_to_primitive(state, config, backend)
        (
            current_density,
            current_velocity,
            current_pressure,
            current_activity,
            current_phase,
        ) = observed
        times.append(time)
        density_history.append(backend.to_numpy(current_density))
        velocity_history.append(backend.to_numpy(current_velocity[0]))
        pressure_history.append(backend.to_numpy(current_pressure))
        activity_history.append(backend.to_numpy(current_activity))
        phase_history.append(backend.to_numpy(current_phase))
        if time >= final_time:
            break
        ####
        timestep = min(
            stable_phase_timestep(state, spacing, 0.26, config, backend),
            5.0e-4,
            final_time - time,
        )
        state = advance_impulsive_phase_euler_split(
            state,
            source,
            timestep,
            spacing,
            config,
            backend,
        )
        time += timestep
    ####

    validation = validate_impulsive_event_history(
        coordinate,
        np.array(times),
        np.stack(density_history),
        np.stack(velocity_history),
        np.stack(pressure_history),
        np.stack(activity_history),
        np.stack(phase_history),
        config,
    )

    assert validation.passed
    assert validation.source_activation_time is not None
    assert validation.pressure_wave_time is not None
    assert validation.phase_onset_time is not None
    assert validation.source_activation_time <= validation.pressure_wave_time
    assert validation.pressure_wave_time <= validation.phase_onset_time
####


def test_two_dimensional_impulse_generates_pressure_motion_and_phase() -> None:
    backend = get_array_backend("numpy")
    config = PhaseEulerConfig(
        heat_release_per_mass=8.0,
        activity_growth_rate=90.0,
        latent_heat_per_mass=1.2,
        transition_temperature=2.2,
        transition_width=0.08,
        phase_relaxation_time=0.012,
    )
    resolution = 32
    coordinate = np.linspace(-1.0, 1.0, resolution, dtype=np.float64)
    x, y = np.meshgrid(coordinate, coordinate, indexing="ij")
    source = np.exp(-0.5 * (x * x + y * y) / 0.15**2)
    density = np.ones((resolution, resolution), dtype=np.float64)
    velocity = np.zeros((2, resolution, resolution), dtype=np.float64)
    pressure = np.ones((resolution, resolution), dtype=np.float64)
    state = primitive_to_phase_conservative(
        density,
        velocity,
        pressure,
        0.015 * source,
        np.zeros_like(source),
        config,
        backend,
    )
    spacing = (float(coordinate[1] - coordinate[0]),) * 2
    time = 0.0
    while time < 0.10:
        timestep = min(
            stable_phase_timestep(state, spacing, 0.24, config, backend),
            5.0e-4,
            0.10 - time,
        )
        state = advance_impulsive_phase_euler_split(
            state,
            source,
            timestep,
            spacing,
            config,
            backend,
        )
        time += timestep
    ####

    final_density, final_velocity, final_pressure, final_activity, final_phase = (
        phase_conservative_to_primitive(state, config, backend)
    )
    speed = np.sqrt(np.sum(final_velocity * final_velocity, axis=0))
    assert np.all(np.isfinite(final_density))
    assert np.all((final_activity >= 0.0) & (final_activity <= 1.0))
    assert np.all((final_phase >= 0.0) & (final_phase <= 1.0))
    assert float(np.max(final_pressure)) > 1.1
    assert float(np.max(final_phase)) > 0.50
    assert float(np.max(speed)) > 0.05
####


def test_three_dimensional_corner_event_generates_pressure_motion_and_phase() -> None:
    backend = get_array_backend("numpy")
    config = PhaseEulerConfig(
        heat_release_per_mass=10.0,
        activity_growth_rate=120.0,
        latent_heat_per_mass=1.4,
        transition_temperature=2.4,
        transition_width=0.08,
        phase_relaxation_time=0.010,
    )
    resolution = 20
    coordinate = np.linspace(-0.95, 0.95, resolution, dtype=np.float64)
    x, y, z = np.meshgrid(coordinate, coordinate, coordinate, indexing="ij")
    source = np.exp(
        -0.5 * ((x + 0.45) ** 2 + (y - 0.45) ** 2 + (z + 0.25) ** 2) / 0.14**2
    )
    density = np.ones(source.shape, dtype=np.float64)
    velocity = np.zeros((3, *source.shape), dtype=np.float64)
    state = primitive_to_phase_conservative(
        density,
        velocity,
        np.ones(source.shape, dtype=np.float64),
        0.015 * source,
        np.zeros(source.shape, dtype=np.float64),
        config,
        backend,
    )
    spacing = (2.0 / resolution,) * 3
    time = 0.0
    while time < 0.08:
        timestep = min(
            stable_phase_timestep(state, spacing, 0.20, config, backend),
            2.0e-4,
            0.08 - time,
        )
        state = advance_impulsive_phase_euler_split(
            state,
            source,
            timestep,
            spacing,
            config,
            backend,
        )
        time += timestep
    ####

    density, velocity, pressure, activity, phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
    )
    speed = np.sqrt(np.sum(velocity * velocity, axis=0))
    assert np.all(np.isfinite(density))
    assert np.all((activity >= 0.0) & (activity <= 1.0))
    assert np.all((phase_fraction >= 0.0) & (phase_fraction <= 1.0))
    assert float(np.max(pressure)) > 1.1
    assert float(np.max(phase_fraction)) > 0.50
    assert float(np.max(speed)) > 0.05
####
