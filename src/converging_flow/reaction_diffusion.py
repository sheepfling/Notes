from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Literal, Protocol, cast

import numpy as np
from numpy.typing import NDArray

ReactionDimension = Literal[1, 2, 3]
ReactionBackend = Literal["numpy", "numba"]
type FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class ReactionDiffusionConfig:
    """Configuration for a generic autocatalytic reaction-diffusion-wave demo."""

    dimensions: ReactionDimension
    resolution: tuple[int, ...]
    backend: ReactionBackend = "numpy"
    half_extent: float = 1.0
    final_time: float = 1.0
    max_steps: int = 100_000
    cfl: float = 0.35
    maximum_timestep: float = 2.0e-3
    activity_diffusivity: float = 0.012
    heat_diffusivity: float = 0.025
    base_growth_rate: float = 2.2
    base_loss_rate: float = 0.55
    catalyst_gain: float = 1.4
    quencher_strength: float = 3.0
    heat_source_rate: float = 1.5
    heat_decay_rate: float = 1.1
    heat_feedback: float = 0.25
    wave_speed: float = 0.65
    wave_damping: float = 1.8
    wave_source_rate: float = 0.9
    seed_width: float = 0.10
    seed_amplitude: float = 0.85
    catalyst_radius: float = 0.42
    quencher_radius: float = 0.78
    transition_width: float = 0.035

    def __post_init__(self) -> None:
        if self.dimensions not in (1, 2, 3):
            raise ValueError("dimensions must be 1, 2, or 3")
        ####
        if self.backend not in ("numpy", "numba"):
            raise ValueError("backend must be 'numpy' or 'numba'")
        ####
        if len(self.resolution) != self.dimensions:
            raise ValueError("resolution length must match dimensions")
        ####
        if any(size < 8 for size in self.resolution):
            raise ValueError("each resolution entry must be at least 8")
        ####
        if self.half_extent <= 0.0:
            raise ValueError("half_extent must be positive")
        ####
        if self.final_time <= 0.0:
            raise ValueError("final_time must be positive")
        ####
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        ####
        if not 0.0 < self.cfl < 1.0:
            raise ValueError("cfl must lie between zero and one")
        ####
        if self.maximum_timestep <= 0.0:
            raise ValueError("maximum_timestep must be positive")
        ####
        if self.activity_diffusivity < 0.0 or self.heat_diffusivity < 0.0:
            raise ValueError("diffusivities cannot be negative")
        ####
        if self.base_growth_rate < 0.0 or self.base_loss_rate < 0.0:
            raise ValueError("reaction rates cannot be negative")
        ####
        if self.catalyst_gain < 0.0 or self.quencher_strength < 0.0:
            raise ValueError("zone strengths cannot be negative")
        ####
        if self.heat_source_rate < 0.0 or self.heat_decay_rate < 0.0:
            raise ValueError("heat rates cannot be negative")
        ####
        if self.heat_feedback < 0.0:
            raise ValueError("heat feedback cannot be negative")
        ####
        if self.wave_speed < 0.0 or self.wave_damping < 0.0:
            raise ValueError("wave parameters cannot be negative")
        ####
        if self.wave_source_rate < 0.0:
            raise ValueError("wave source rate cannot be negative")
        ####
        if self.seed_width <= 0.0:
            raise ValueError("seed_width must be positive")
        ####
        if not 0.0 <= self.seed_amplitude <= 1.0:
            raise ValueError("seed_amplitude must lie between zero and one")
        ####
        if not 0.0 < self.catalyst_radius < self.quencher_radius < self.half_extent:
            raise ValueError(
                "radii must satisfy 0 < catalyst_radius < quencher_radius < half_extent"
            )
        ####
        if self.transition_width <= 0.0:
            raise ValueError("transition_width must be positive")
        ####
    ####

    @property
    def spacing(self) -> tuple[float, ...]:
        return tuple(2.0 * self.half_extent / size for size in self.resolution)
    ####
####


@dataclass(frozen=True, slots=True)
class ReactionDiagnostics:
    time: float
    step: int
    total_activity: float
    maximum_activity: float
    maximum_heat: float
    wave_rms: float
    active_volume_fraction: float
####


@dataclass(frozen=True, slots=True)
class ReactionFrame:
    time: float
    activity: FloatArray
    heat: FloatArray
    wave: FloatArray
####


@dataclass(frozen=True, slots=True)
class ReactionResult:
    config: ReactionDiffusionConfig
    coordinates: tuple[FloatArray, ...]
    activity: FloatArray
    heat: FloatArray
    wave: FloatArray
    wave_velocity: FloatArray
    catalyst: FloatArray
    quencher: FloatArray
    time: float
    steps: int
    initial_diagnostics: ReactionDiagnostics
    final_diagnostics: ReactionDiagnostics
    frames: tuple[ReactionFrame, ...] = ()
####


class ReactionStepper(Protocol):
    """Advance one prepared reaction-diffusion-wave system."""

    def step(
        self,
        activity: FloatArray,
        heat: FloatArray,
        wave: FloatArray,
        wave_velocity: FloatArray,
        timestep: float,
    ) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]: ...
####


def reaction_cell_centers(
    config: ReactionDiffusionConfig,
) -> tuple[FloatArray, ...]:
    coordinates: list[FloatArray] = []
    for size, spacing in zip(config.resolution, config.spacing, strict=True):
        coordinates.append(
            np.linspace(
                -config.half_extent + 0.5 * spacing,
                config.half_extent - 0.5 * spacing,
                size,
                dtype=np.float64,
            )
        )
    ####
    return tuple(coordinates)
####


def _radius_field(
    coordinates: tuple[FloatArray, ...],
    shape: tuple[int, ...],
) -> FloatArray:
    radius_squared = np.zeros(shape, dtype=np.float64)
    for coordinate in np.meshgrid(*coordinates, indexing="ij", sparse=True):
        radius_squared += coordinate * coordinate
    ####
    return np.sqrt(radius_squared)
####


def initialize_reaction_fields(
    config: ReactionDiffusionConfig,
) -> tuple[
    tuple[FloatArray, ...],
    FloatArray,
    FloatArray,
    FloatArray,
    FloatArray,
    FloatArray,
    FloatArray,
]:
    coordinates = reaction_cell_centers(config)
    radius = _radius_field(coordinates, config.resolution)

    activity = config.seed_amplitude * np.exp(
        -0.5 * (radius / config.seed_width) ** 2
    )
    heat = np.zeros(config.resolution, dtype=np.float64)
    wave = np.zeros(config.resolution, dtype=np.float64)
    wave_velocity = np.zeros(config.resolution, dtype=np.float64)

    catalyst = 0.5 * (
        1.0
        - np.tanh(
            (radius - config.catalyst_radius) / config.transition_width
        )
    )
    quencher = 0.5 * (
        1.0
        + np.tanh(
            (radius - config.quencher_radius) / config.transition_width
        )
    )
    return (
        coordinates,
        activity,
        heat,
        wave,
        wave_velocity,
        catalyst,
        quencher,
    )
####


def neumann_laplacian(
    values: FloatArray,
    spacing: tuple[float, ...],
) -> FloatArray:
    """Return a vectorized second-order Laplacian with zero-normal-gradient walls."""
    if values.ndim != len(spacing):
        raise ValueError("spacing length must match values.ndim")
    ####

    padded = np.pad(values, 1, mode="edge")
    center_slices = tuple(slice(1, -1) for _ in range(values.ndim))
    center = padded[center_slices]
    laplacian = np.zeros_like(values)

    for axis, delta in enumerate(spacing):
        lower = list(center_slices)
        upper = list(center_slices)
        lower[axis] = slice(0, -2)
        upper[axis] = slice(2, None)
        laplacian += (
            padded[tuple(lower)] - 2.0 * center + padded[tuple(upper)]
        ) / (delta * delta)
    ####
    return laplacian
####


def _right_hand_side_prepared(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    local_growth: FloatArray,
    local_loss: FloatArray,
    config: ReactionDiffusionConfig,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    activity_laplacian = neumann_laplacian(activity, config.spacing)
    heat_laplacian = neumann_laplacian(heat, config.spacing)
    wave_laplacian = neumann_laplacian(wave, config.spacing)

    saturation = np.maximum(1.0 - activity, 0.0)

    activity_rate = (
        config.activity_diffusivity * activity_laplacian
        + local_growth * activity * saturation
        + config.heat_feedback * heat * saturation
        - local_loss * activity
    )
    heat_rate = (
        config.heat_diffusivity * heat_laplacian
        + config.heat_source_rate * activity
        - config.heat_decay_rate * heat
    )
    wave_rate = wave_velocity
    wave_velocity_rate = (
        config.wave_speed * config.wave_speed * wave_laplacian
        + config.wave_source_rate * activity
        - config.wave_damping * wave_velocity
    )
    return activity_rate, heat_rate, wave_rate, wave_velocity_rate
####


def _right_hand_side(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    catalyst: FloatArray,
    quencher: FloatArray,
    config: ReactionDiffusionConfig,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    local_growth = config.base_growth_rate * (
        1.0 + config.catalyst_gain * catalyst
    )
    local_loss = config.base_loss_rate + config.quencher_strength * quencher
    return _right_hand_side_prepared(
        activity,
        heat,
        wave,
        wave_velocity,
        local_growth,
        local_loss,
        config,
    )
####


def stable_reaction_timestep(config: ReactionDiffusionConfig) -> float:
    minimum_spacing = min(config.spacing)
    dimensionality = float(config.dimensions)
    maximum_diffusivity = max(
        config.activity_diffusivity,
        config.heat_diffusivity,
    )

    diffusion_limit = np.inf
    if maximum_diffusivity > 0.0:
        diffusion_limit = (
            config.cfl
            * minimum_spacing
            * minimum_spacing
            / (2.0 * dimensionality * maximum_diffusivity)
        )
    ####

    wave_limit = np.inf
    if config.wave_speed > 0.0:
        wave_limit = (
            config.cfl
            * minimum_spacing
            / (config.wave_speed * np.sqrt(dimensionality))
        )
    ####

    reaction_scale = (
        config.base_growth_rate * (1.0 + config.catalyst_gain)
        + config.base_loss_rate
        + config.quencher_strength
        + config.heat_decay_rate
        + config.wave_damping
    )
    reaction_limit = np.inf
    if reaction_scale > 0.0:
        reaction_limit = config.cfl / reaction_scale
    ####

    return float(
        min(
            config.maximum_timestep,
            diffusion_limit,
            wave_limit,
            reaction_limit,
        )
    )
####


def _advance_reaction_fields_prepared(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    local_growth: FloatArray,
    local_loss: FloatArray,
    config: ReactionDiffusionConfig,
    timestep: float,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    if timestep <= 0.0:
        raise ValueError("timestep must be positive")
    ####

    rate_1 = _right_hand_side_prepared(
        activity,
        heat,
        wave,
        wave_velocity,
        local_growth,
        local_loss,
        config,
    )
    midpoint = tuple(
        field + 0.5 * timestep * rate
        for field, rate in zip(
            (activity, heat, wave, wave_velocity),
            rate_1,
            strict=True,
        )
    )
    midpoint_activity = np.clip(midpoint[0], 0.0, 1.0)
    midpoint_heat = np.maximum(midpoint[1], 0.0)

    rate_2 = _right_hand_side_prepared(
        midpoint_activity,
        midpoint_heat,
        midpoint[2],
        midpoint[3],
        local_growth,
        local_loss,
        config,
    )
    next_fields = tuple(
        field + timestep * rate
        for field, rate in zip(
            (activity, heat, wave, wave_velocity),
            rate_2,
            strict=True,
        )
    )
    return (
        np.clip(next_fields[0], 0.0, 1.0),
        np.maximum(next_fields[1], 0.0),
        next_fields[2],
        next_fields[3],
    )
####


def advance_reaction_fields(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    catalyst: FloatArray,
    quencher: FloatArray,
    config: ReactionDiffusionConfig,
    timestep: float,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Advance fields with the portable vectorized midpoint implementation."""
    local_growth = config.base_growth_rate * (
        1.0 + config.catalyst_gain * catalyst
    )
    local_loss = config.base_loss_rate + config.quencher_strength * quencher
    return _advance_reaction_fields_prepared(
        activity,
        heat,
        wave,
        wave_velocity,
        local_growth,
        local_loss,
        config,
        timestep,
    )
####


@dataclass(slots=True)
class NumpyReactionStepper:
    """Prepared NumPy backend with static coefficient fields cached once."""

    config: ReactionDiffusionConfig
    local_growth: FloatArray
    local_loss: FloatArray

    @classmethod
    def create(
        cls,
        config: ReactionDiffusionConfig,
        catalyst: FloatArray,
        quencher: FloatArray,
    ) -> NumpyReactionStepper:
        return cls(
            config=config,
            local_growth=config.base_growth_rate
            * (1.0 + config.catalyst_gain * catalyst),
            local_loss=config.base_loss_rate
            + config.quencher_strength * quencher,
        )
    ####

    def step(
        self,
        activity: FloatArray,
        heat: FloatArray,
        wave: FloatArray,
        wave_velocity: FloatArray,
        timestep: float,
    ) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
        return _advance_reaction_fields_prepared(
            activity,
            heat,
            wave,
            wave_velocity,
            self.local_growth,
            self.local_loss,
            self.config,
            timestep,
        )
    ####
####


def _build_reaction_stepper(
    config: ReactionDiffusionConfig,
    activity: FloatArray,
    catalyst: FloatArray,
    quencher: FloatArray,
) -> ReactionStepper:
    if config.backend == "numpy":
        return NumpyReactionStepper.create(config, catalyst, quencher)
    ####

    try:
        module = import_module("converging_flow.reaction_numba")
    except ImportError as error:
        raise RuntimeError(
            "the numba backend requires the optional 'fast' dependency: "
            "pip install '.[fast]' from the repository root"
        ) from error
    ####

    stepper_type = cast(Any, module).NumbaReactionStepper
    return cast(
        ReactionStepper,
        stepper_type.create(config, activity, catalyst, quencher),
    )
####


def reaction_diagnostics(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    config: ReactionDiffusionConfig,
    time: float,
    step: int,
) -> ReactionDiagnostics:
    cell_volume = float(np.prod(config.spacing))
    return ReactionDiagnostics(
        time=time,
        step=step,
        total_activity=float(np.sum(activity) * cell_volume),
        maximum_activity=float(np.max(activity)),
        maximum_heat=float(np.max(heat)),
        wave_rms=float(np.sqrt(np.mean(wave * wave))),
        active_volume_fraction=float(np.mean(activity >= 0.10)),
    )
####


def _visualization_field(values: FloatArray) -> FloatArray:
    if values.ndim < 3:
        return values.copy()
    ####
    return values[:, :, values.shape[2] // 2].copy()
####


def _make_reaction_frame(
    time: float,
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
) -> ReactionFrame:
    return ReactionFrame(
        time=time,
        activity=_visualization_field(activity),
        heat=_visualization_field(heat),
        wave=_visualization_field(wave),
    )
####


def run_reaction_diffusion(
    config: ReactionDiffusionConfig,
    snapshot_count: int = 0,
) -> ReactionResult:
    if snapshot_count == 1 or snapshot_count < 0:
        raise ValueError("snapshot_count must be zero or at least two")
    ####

    (
        coordinates,
        activity,
        heat,
        wave,
        wave_velocity,
        catalyst,
        quencher,
    ) = initialize_reaction_fields(config)
    time = 0.0
    step = 0
    initial_diagnostics = reaction_diagnostics(
        activity,
        heat,
        wave,
        config,
        time,
        step,
    )

    frames: list[ReactionFrame] = []
    target_times = np.empty(0, dtype=np.float64)
    next_target = 0
    if snapshot_count >= 2:
        target_times = np.linspace(0.0, config.final_time, snapshot_count)
        frames.append(_make_reaction_frame(time, activity, heat, wave))
        next_target = 1
    ####

    stepper = _build_reaction_stepper(
        config,
        activity,
        catalyst,
        quencher,
    )
    base_timestep = stable_reaction_timestep(config)
    while time < config.final_time and step < config.max_steps:
        timestep = min(base_timestep, config.final_time - time)
        activity, heat, wave, wave_velocity = stepper.step(
            activity,
            heat,
            wave,
            wave_velocity,
            timestep,
        )
        time += timestep
        step += 1

        while next_target < snapshot_count and time >= target_times[next_target] - 1.0e-14:
            frames.append(_make_reaction_frame(time, activity, heat, wave))
            next_target += 1
        ####
    ####

    if time < config.final_time:
        raise RuntimeError(
            f"maximum step count reached at t={time:.6g}, target={config.final_time:.6g}"
        )
    ####

    final_diagnostics = reaction_diagnostics(
        activity,
        heat,
        wave,
        config,
        time,
        step,
    )
    return ReactionResult(
        config=config,
        coordinates=coordinates,
        activity=activity,
        heat=heat,
        wave=wave,
        wave_velocity=wave_velocity,
        catalyst=catalyst,
        quencher=quencher,
        time=time,
        steps=step,
        initial_diagnostics=initial_diagnostics,
        final_diagnostics=final_diagnostics,
        frames=tuple(frames),
    )
####


def reaction_config(
    dimensions: int,
    resolution: int,
    final_time: float,
    backend: ReactionBackend = "numpy",
) -> ReactionDiffusionConfig:
    return ReactionDiffusionConfig(
        dimensions=cast(ReactionDimension, dimensions),
        resolution=(resolution,) * dimensions,
        final_time=final_time,
        backend=backend,
    )
####
