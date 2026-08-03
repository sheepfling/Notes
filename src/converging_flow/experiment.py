from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from converging_flow.backend import ResolvedBackendName, get_array_backend
from converging_flow.config import SimulationConfig
from converging_flow.euler import (
    FloatArray,
    conservative_to_primitive,
    primitive_to_conservative,
)
from converging_flow.euler_backend import (
    advance_rusanov_backend,
    stable_timestep_backend,
)

type IntArray = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class Diagnostics:
    time: float
    step: int
    mass: float
    total_energy: float
    minimum_density: float
    minimum_pressure: float
    maximum_mach: float
####


@dataclass(frozen=True, slots=True)
class RadialProfile:
    radius: FloatArray
    density: FloatArray
    pressure: FloatArray
    speed: FloatArray
    radial_velocity: FloatArray
    mach: FloatArray
    density_standard_deviation: FloatArray
    pressure_standard_deviation: FloatArray
####


@dataclass(frozen=True, slots=True)
class VisualizationFrame:
    time: float
    density_field: FloatArray
    pressure_field: FloatArray
    speed_field: FloatArray
    radial_velocity_field: FloatArray
    radial_profile: RadialProfile
####


@dataclass(frozen=True, slots=True)
class SimulationResult:
    config: SimulationConfig
    resolved_backend: ResolvedBackendName
    coordinates: tuple[FloatArray, ...]
    state: FloatArray
    time: float
    steps: int
    initial_diagnostics: Diagnostics
    final_diagnostics: Diagnostics
    frames: tuple[VisualizationFrame, ...] = ()
####


def cell_centers(config: SimulationConfig) -> tuple[FloatArray, ...]:
    coordinates: list[FloatArray] = []
    for size, dx in zip(config.resolution, config.spacing, strict=True):
        coordinates.append(
            np.linspace(
                -config.half_extent + 0.5 * dx,
                config.half_extent - 0.5 * dx,
                size,
                dtype=np.float64,
            )
        )
    ####
    return tuple(coordinates)
####


def initialize_state(config: SimulationConfig) -> tuple[tuple[FloatArray, ...], FloatArray]:
    """Create a smooth inert gas shell with inward radial velocity."""
    coordinates = cell_centers(config)
    mesh = np.meshgrid(*coordinates, indexing="ij", sparse=True)
    radius_squared = np.zeros(config.resolution, dtype=np.float64)
    for coordinate in mesh:
        radius_squared += coordinate * coordinate
    ####
    radius = np.sqrt(radius_squared)

    density = np.full(config.resolution, config.ambient_density, dtype=np.float64)
    pressure = np.full(config.resolution, config.ambient_pressure, dtype=np.float64)
    velocity = np.zeros((config.dimensions, *config.resolution), dtype=np.float64)

    shell_profile = np.exp(
        -0.5 * ((radius - config.shell_radius) / config.shell_width) ** 2
    )
    sound_speed = np.sqrt(
        config.gamma * config.ambient_pressure / config.ambient_density
    )
    inward_speed = config.inward_mach * sound_speed * shell_profile
    safe_radius = np.where(radius > 0.0, radius, 1.0)

    for axis, coordinate in enumerate(mesh):
        velocity[axis] = -inward_speed * coordinate / safe_radius
    ####

    state = primitive_to_conservative(density, velocity, pressure, config.gamma)
    return coordinates, state
####


def compute_diagnostics(
    state: FloatArray,
    config: SimulationConfig,
    time: float,
    step: int,
) -> Diagnostics:
    density, velocity, pressure = conservative_to_primitive(
        state,
        config.gamma,
        config.density_floor,
        config.pressure_floor,
    )
    cell_volume = float(np.prod(config.spacing))
    sound_speed = np.sqrt(config.gamma * pressure / density)
    speed = np.sqrt(np.sum(velocity * velocity, axis=0))
    mach = speed / sound_speed

    return Diagnostics(
        time=time,
        step=step,
        mass=float(np.sum(density) * cell_volume),
        total_energy=float(np.sum(state[-1]) * cell_volume),
        minimum_density=float(np.min(density)),
        minimum_pressure=float(np.min(pressure)),
        maximum_mach=float(np.max(mach)),
    )
####


def _radial_geometry(
    coordinates: tuple[FloatArray, ...],
    shape: tuple[int, ...],
) -> tuple[list[FloatArray], FloatArray]:
    mesh = list(np.meshgrid(*coordinates, indexing="ij", sparse=True))
    radius_squared = np.zeros(shape, dtype=np.float64)
    for coordinate in mesh:
        radius_squared += coordinate * coordinate
    ####
    return mesh, np.sqrt(radius_squared)
####


def _radial_profile_from_primitive(
    coordinates: tuple[FloatArray, ...],
    density: FloatArray,
    velocity: FloatArray,
    pressure: FloatArray,
    gamma: float,
    half_extent: float,
    bins: int,
) -> RadialProfile:
    if bins < 4:
        raise ValueError("bins must be at least 4")
    ####

    mesh, radius = _radial_geometry(coordinates, density.shape)
    speed = np.sqrt(np.sum(velocity * velocity, axis=0))
    safe_radius = np.where(radius > 0.0, radius, 1.0)
    radial_velocity = np.zeros_like(density)
    for axis, coordinate in enumerate(mesh):
        radial_velocity += velocity[axis] * coordinate / safe_radius
    ####
    radial_velocity = np.where(radius > 0.0, radial_velocity, 0.0)
    sound_speed = np.sqrt(gamma * pressure / density)
    mach = speed / sound_speed

    bin_edges = np.linspace(0.0, half_extent, bins + 1, dtype=np.float64)
    centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    flat_radius = radius.ravel()
    inside = flat_radius <= half_extent
    selected_radius = flat_radius[inside]
    indices = np.clip(
        np.digitize(selected_radius, bin_edges) - 1,
        0,
        bins - 1,
    ).astype(np.int64, copy=False)
    counts = np.bincount(indices, minlength=bins).astype(np.float64)
    populated = counts > 0.0

    def shell_moments(values: FloatArray) -> tuple[FloatArray, FloatArray]:
        selected_values = values.ravel()[inside]
        sums = np.bincount(
            indices,
            weights=selected_values,
            minlength=bins,
        )
        square_sums = np.bincount(
            indices,
            weights=selected_values * selected_values,
            minlength=bins,
        )
        sampled_mean = sums[populated] / counts[populated]
        sampled_variance = (
            square_sums[populated] / counts[populated] - sampled_mean * sampled_mean
        )
        sampled_standard_deviation = np.sqrt(np.maximum(sampled_variance, 0.0))
        return (
            np.interp(centers, centers[populated], sampled_mean),
            np.interp(centers, centers[populated], sampled_standard_deviation),
        )
    ####

    density_mean, density_standard_deviation = shell_moments(density)
    pressure_mean, pressure_standard_deviation = shell_moments(pressure)
    speed_mean, _ = shell_moments(speed)
    radial_velocity_mean, _ = shell_moments(radial_velocity)
    mach_mean, _ = shell_moments(mach)

    return RadialProfile(
        radius=centers,
        density=density_mean,
        pressure=pressure_mean,
        speed=speed_mean,
        radial_velocity=radial_velocity_mean,
        mach=mach_mean,
        density_standard_deviation=density_standard_deviation,
        pressure_standard_deviation=pressure_standard_deviation,
    )
####


def radial_profile_data(
    result: SimulationResult,
    bins: int = 128,
) -> RadialProfile:
    """Return shell-averaged scalar and radial-flow observables."""
    density, velocity, pressure = conservative_to_primitive(
        result.state,
        result.config.gamma,
        result.config.density_floor,
        result.config.pressure_floor,
    )
    return _radial_profile_from_primitive(
        result.coordinates,
        density,
        velocity,
        pressure,
        result.config.gamma,
        result.config.half_extent,
        bins,
    )
####


def radial_profile(
    result: SimulationResult,
    bins: int = 128,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Return the original density, pressure, and speed radial-profile tuple."""
    profile = radial_profile_data(result, bins)
    return profile.radius, profile.density, profile.pressure, profile.speed
####


def _central_visualization_field(values: FloatArray, dimensions: int) -> FloatArray:
    if dimensions < 3:
        return values.copy()
    ####
    middle = values.shape[2] // 2
    return values[:, :, middle].copy()
####


def _make_visualization_frame(
    state: FloatArray,
    coordinates: tuple[FloatArray, ...],
    config: SimulationConfig,
    time: float,
) -> VisualizationFrame:
    density, velocity, pressure = conservative_to_primitive(
        state,
        config.gamma,
        config.density_floor,
        config.pressure_floor,
    )
    speed = np.sqrt(np.sum(velocity * velocity, axis=0))
    mesh, radius = _radial_geometry(coordinates, density.shape)
    safe_radius = np.where(radius > 0.0, radius, 1.0)
    radial_velocity = np.zeros_like(density)
    for axis, coordinate in enumerate(mesh):
        radial_velocity += velocity[axis] * coordinate / safe_radius
    ####
    radial_velocity = np.where(radius > 0.0, radial_velocity, 0.0)

    return VisualizationFrame(
        time=time,
        density_field=_central_visualization_field(density, config.dimensions),
        pressure_field=_central_visualization_field(pressure, config.dimensions),
        speed_field=_central_visualization_field(speed, config.dimensions),
        radial_velocity_field=_central_visualization_field(
            radial_velocity,
            config.dimensions,
        ),
        radial_profile=_radial_profile_from_primitive(
            coordinates,
            density,
            velocity,
            pressure,
            config.gamma,
            config.half_extent,
            bins=128,
        ),
    )
####


def run_simulation(
    config: SimulationConfig,
    snapshot_count: int = 0,
) -> SimulationResult:
    if snapshot_count == 1 or snapshot_count < 0:
        raise ValueError("snapshot_count must be zero or at least two")
    ####

    coordinates, initial_state = initialize_state(config)
    backend = get_array_backend(config.backend)
    state = backend.asarray(initial_state)
    time = 0.0
    step = 0
    initial_diagnostics = compute_diagnostics(initial_state, config, time, step)

    frames: list[VisualizationFrame] = []
    target_times = np.empty(0, dtype=np.float64)
    next_target = 0
    if snapshot_count >= 2:
        target_times = np.linspace(0.0, config.final_time, snapshot_count)
        frames.append(
            _make_visualization_frame(
                backend.to_numpy(state),
                coordinates,
                config,
                time,
            )
        )
        next_target = 1
    ####

    while time < config.final_time and step < config.max_steps:
        timestep = stable_timestep_backend(
            state,
            config.spacing,
            config.gamma,
            config.cfl,
            config.density_floor,
            config.pressure_floor,
            backend,
        )
        timestep = min(timestep, config.final_time - time)
        state = advance_rusanov_backend(
            state,
            timestep,
            config.spacing,
            config.gamma,
            config.density_floor,
            config.pressure_floor,
            backend,
        )
        time += timestep
        step += 1

        while next_target < snapshot_count and time >= target_times[next_target] - 1.0e-14:
            frames.append(
                _make_visualization_frame(
                    backend.to_numpy(state),
                    coordinates,
                    config,
                    time,
                )
            )
            next_target += 1
        ####
    ####

    if time < config.final_time:
        raise RuntimeError(
            f"maximum step count reached at t={time:.6g}, target={config.final_time:.6g}"
        )
    ####

    backend.synchronize()
    final_state = backend.to_numpy(state)
    final_diagnostics = compute_diagnostics(final_state, config, time, step)
    return SimulationResult(
        config=config,
        resolved_backend=backend.name,
        coordinates=coordinates,
        state=final_state,
        time=time,
        steps=step,
        initial_diagnostics=initial_diagnostics,
        final_diagnostics=final_diagnostics,
        frames=tuple(frames),
    )
####
