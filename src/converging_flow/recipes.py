"""Reusable, parameterized experiment recipes built from generic primitives."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from converging_flow.backend import BackendName
from converging_flow.geometry import (
    axial_half_mask,
    perforated_block_masks,
    spherical_shell_mask,
)
from converging_flow.material_events import (
    LinearRamp,
    MaterialEventSchedule,
    MaterialPropertyRamp,
    MaterialReplacementEvent,
)
from converging_flow.phase_euler import PhaseEulerConfig
from converging_flow.radiant_wave import (
    ABSORBER_ID,
    CHANNEL_ID,
    NEUTRAL_ID,
    REFLECTOR_ID,
    MaterialProperties,
    RadiantWaveConfig,
    cell_centers,
)
from converging_flow.reactive_euler import ReactiveEulerConfig


@dataclass(frozen=True, slots=True)
class RadiantMaterialParameters:
    """Normalized thermal, reactive, and scalar-wave properties of one material."""

    activity_diffusivity: float
    growth_rate: float
    loss_rate: float
    thermal_conductivity: float
    specific_heat: float
    heat_loss_rate: float
    wave_density: float
    wave_stiffness: float
    wave_damping: float

    def material_properties(self) -> MaterialProperties:
        return MaterialProperties(
            activity_diffusivity=self.activity_diffusivity,
            growth_rate=self.growth_rate,
            loss_rate=self.loss_rate,
            thermal_conductivity=self.thermal_conductivity,
            heat_capacity=self.specific_heat,
            heat_loss_rate=self.heat_loss_rate,
            wave_density=self.wave_density,
            wave_stiffness=self.wave_stiffness,
            wave_damping=self.wave_damping,
        )
    ####
####


@dataclass(frozen=True, slots=True)
class RadiantMaterialSet:
    """Named material data used by a scalar-wave experiment recipe."""

    reflector: RadiantMaterialParameters = field(
        default_factory=lambda: RadiantMaterialParameters(
            0.010, 2.35, 0.45, 0.018, 1.10, 0.75, 4.0, 4.0 * 0.65**2, 0.08
        )
    )
    active_medium: RadiantMaterialParameters = field(
        default_factory=lambda: RadiantMaterialParameters(
            0.012, 2.20, 0.55, 0.025, 1.00, 1.10, 1.0, 0.65**2, 0.20
        )
    )
    loss_material: RadiantMaterialParameters = field(
        default_factory=lambda: RadiantMaterialParameters(
            0.006, 1.45, 2.80, 0.040, 1.40, 2.20, 1.0, 0.65**2, 4.50
        )
    )
    open_passage: RadiantMaterialParameters = field(
        default_factory=lambda: RadiantMaterialParameters(
            0.020, 0.0, 0.35, 0.060, 0.60, 0.25, 1.0, 0.65**2, 0.08
        )
    )
####


@dataclass(frozen=True, slots=True)
class RadiantSourceParameters:
    """Normalized source and feedback coefficients for the scalar-wave model."""

    heat_source_rate: float = 1.50
    heat_feedback: float = 0.25
    wave_source_rate: float = 0.90
    wave_pressure_feedback: float = 0.08
    seed_width: float = 0.38
    seed_amplitude: float = 0.85
####


@dataclass(frozen=True, slots=True)
class PerforatedBlockParameters:
    """Data-only recipe for a perforated block and time-ramped loss rods."""

    resolution: int = 56
    backend: BackendName = "auto"
    half_extent: float = 1.0
    final_time: float = 0.24
    cfl: float = 0.30
    maximum_timestep: float = 2.0e-3
    channel_counts: tuple[int, int] = (6, 4)
    block_fraction: float = 0.82
    channel_radius_fraction: float = 0.065
    insertion_start_time: float = 0.05
    insertion_end_time: float = 0.12
    insertion_fraction: float = 0.50
    thermal_exchange: float = 12.0
    source_scale: float = 0.5
    loss_scale: float = 120.0
    materials: RadiantMaterialSet = field(default_factory=RadiantMaterialSet)
    source: RadiantSourceParameters = field(default_factory=RadiantSourceParameters)
####


@dataclass(frozen=True, slots=True)
class ShellRelaxationParameters:
    """Data-only recipe for a shell with a scheduled half-space loss event."""

    resolution: int = 48
    backend: BackendName = "auto"
    half_extent: float = 1.0
    shell_radius_fraction: float = 0.72
    final_time: float = 0.06
    insertion_time: float = 0.03
    source_scale: float = 3.0
    loss_scale: float = 12.0
    materials: RadiantMaterialSet = field(default_factory=RadiantMaterialSet)
    source: RadiantSourceParameters = field(default_factory=RadiantSourceParameters)
####


@dataclass(frozen=True, slots=True)
class PhaseThermalParameters:
    """EOS, heat-release, and phase-change data for normalized Euler stages.

    ``phase_change_energy_per_mass`` is the latent heat of vaporization or
    transformation in normalized units. ``specific_heat`` and ``gas_constant``
    determine ``gamma = 1 + R / c_v``; their defaults preserve ``gamma = 1.4``.
    """

    specific_heat: float = 2.5
    gas_constant: float = 1.0
    heat_release_per_mass: float = 6.0
    activity_growth_rate: float = 75.0
    phase_change_energy_per_mass: float = 1.0
    transition_temperature: float = 2.0
    transition_width: float = 0.08
    phase_relaxation_time: float = 0.012

    def phase_config(self) -> PhaseEulerConfig:
        return PhaseEulerConfig(
            gamma=1.0 + self.gas_constant / self.specific_heat,
            gas_constant=self.gas_constant,
            specific_heat=self.specific_heat,
            heat_release_per_mass=self.heat_release_per_mass,
            activity_growth_rate=self.activity_growth_rate,
            latent_heat_per_mass=self.phase_change_energy_per_mass,
            transition_temperature=self.transition_temperature,
            transition_width=self.transition_width,
            phase_relaxation_time=self.phase_relaxation_time,
        )
    ####
####


@dataclass(frozen=True, slots=True)
class InitialStateParameters:
    """Uniform Euler initial state and precursor-to-pressure handoff scale."""

    density: float = 1.0
    pressure: float = 1.0
    activity_seed_fraction: float = 0.015
    heat_pressure_offset: float = 0.04
####


@dataclass(frozen=True, slots=True)
class EventFootprintParameters:
    """Location, extent, and activation time of a normalized event."""

    center: tuple[float, float, float] = (-0.50, 0.52, -0.30)
    width: float = 0.14
    activation_time: float = 0.035
    final_time: float = 0.16
####


@dataclass(frozen=True, slots=True)
class CouplingParameters:
    """Weights used to form a normalized cross-solver permission field."""

    activity_weight: float = 0.35
    heat_weight: float = 0.25
    wave_pressure_weight: float = 0.15
    baseline: float = 0.25
####


@dataclass(frozen=True, slots=True)
class EulerNumericsParameters:
    """CFL and timestep limits for an Euler event stage."""

    cfl: float = 0.20
    maximum_timestep: float = 2.0e-4
####


@dataclass(frozen=True, slots=True)
class EventValidationParameters:
    """Expected qualitative outcomes used for regression validation."""

    minimum_pressure_rise: float = 0.10
    minimum_phase_fraction: float = 0.50
    minimum_speed: float = 0.05
    require_causal_order: bool = True
####


@dataclass(frozen=True, slots=True)
class PresentationParameters:
    """Artifact sampling and animation controls."""

    frames: int = 101
    fps: int = 16
####


@dataclass(frozen=True, slots=True)
class PerforatedBlockEventParameters:
    """Complete data-only specification of the 3D staged-event experiment."""

    precursor: PerforatedBlockParameters = field(
        default_factory=lambda: PerforatedBlockParameters(resolution=48)
    )
    initial_state: InitialStateParameters = field(default_factory=InitialStateParameters)
    event: EventFootprintParameters = field(default_factory=EventFootprintParameters)
    coupling: CouplingParameters = field(default_factory=CouplingParameters)
    phase: PhaseThermalParameters = field(
        default_factory=lambda: PhaseThermalParameters(
            heat_release_per_mass=10.0,
            activity_growth_rate=120.0,
            phase_change_energy_per_mass=1.4,
            transition_temperature=2.4,
            phase_relaxation_time=0.010,
        )
    )
    numerics: EulerNumericsParameters = field(default_factory=EulerNumericsParameters)
    validation: EventValidationParameters = field(
        default_factory=lambda: EventValidationParameters(
            minimum_pressure_rise=0.10,
            minimum_phase_fraction=0.50,
            minimum_speed=0.05,
        )
    )
    presentation: PresentationParameters = field(default_factory=PresentationParameters)
####


def _material_set_from_mapping(
    values: Mapping[str, Any],
    defaults: RadiantMaterialSet,
) -> RadiantMaterialSet:
    default_values = asdict(defaults)
    merged: dict[str, RadiantMaterialParameters] = {}
    for name, default in default_values.items():
        override = values.get(name, {})
        if not isinstance(override, Mapping):
            raise TypeError(f"materials.{name} must be a JSON object")
        ####
        merged[name] = RadiantMaterialParameters(**(default | dict(override)))
    ####
    return RadiantMaterialSet(**merged)
####


def _source_from_mapping(
    values: Mapping[str, Any],
    defaults: RadiantSourceParameters,
) -> RadiantSourceParameters:
    return RadiantSourceParameters(**(asdict(defaults) | dict(values)))
####


def _load_parameter_mapping(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as error:
            raise RuntimeError(
                "YAML parameter files require the optional PyYAML dependency; "
                "use JSON or install the project's dev dependencies"
            ) from error
        ####
        values = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        values = json.loads(path.read_text(encoding="utf-8"))
    ####
    if not isinstance(values, dict):
        raise TypeError("recipe parameter file must contain an object")
    ####
    return values
####


def _perforated_block_parameters_from_mapping(
    values: dict[str, Any],
) -> PerforatedBlockParameters:
    defaults = PerforatedBlockParameters()
    if "channel_counts" in values:
        values["channel_counts"] = tuple(values["channel_counts"])
    ####
    materials = _material_set_from_mapping(
        values.pop("materials", {}), defaults.materials
    )
    source = _source_from_mapping(values.pop("source", {}), defaults.source)
    return PerforatedBlockParameters(
        **(asdict(defaults) | values | {"materials": materials, "source": source})
    )
####


def perforated_block_parameters_from_json(path: Path) -> PerforatedBlockParameters:
    """Load a perforated-block recipe from a JSON or optional YAML file."""
    return _perforated_block_parameters_from_mapping(_load_parameter_mapping(path))
####


def shell_relaxation_parameters_from_json(path: Path) -> ShellRelaxationParameters:
    """Load a shell-relaxation recipe from a portable JSON parameter file."""
    values = _load_parameter_mapping(path)
    defaults = ShellRelaxationParameters()
    materials = _material_set_from_mapping(
        values.pop("materials", {}), defaults.materials
    )
    source = _source_from_mapping(values.pop("source", {}), defaults.source)
    return ShellRelaxationParameters(
        **(asdict(defaults) | values | {"materials": materials, "source": source})
    )
####


def perforated_block_event_parameters_from_file(
    path: Path,
) -> PerforatedBlockEventParameters:
    """Load the full staged 3D experiment document from JSON or optional YAML."""
    values = _load_parameter_mapping(path)
    defaults = PerforatedBlockEventParameters()
    precursor_values = values.pop("precursor", {})
    if not isinstance(precursor_values, dict):
        raise TypeError("precursor must be an object")
    ####
    event_values = values.pop("event", {})
    if not isinstance(event_values, dict):
        raise TypeError("event must be an object")
    ####
    if "center" in event_values:
        event_values["center"] = tuple(event_values["center"])
    ####

    def section(name: str, constructor: type[Any], default: Any) -> Any:
        section_values = values.pop(name, {})
        if not isinstance(section_values, dict):
            raise TypeError(f"{name} must be an object")
        ####
        return constructor(**(asdict(default) | section_values))
    ####

    return PerforatedBlockEventParameters(
        precursor=_perforated_block_parameters_from_mapping(precursor_values),
        initial_state=section(
            "initial_state", InitialStateParameters, defaults.initial_state
        ),
        event=EventFootprintParameters(**(asdict(defaults.event) | event_values)),
        coupling=section("coupling", CouplingParameters, defaults.coupling),
        phase=section("phase", PhaseThermalParameters, defaults.phase),
        numerics=section("numerics", EulerNumericsParameters, defaults.numerics),
        validation=section(
            "validation", EventValidationParameters, defaults.validation
        ),
        presentation=section(
            "presentation", PresentationParameters, defaults.presentation
        ),
        **values,
    )
####


def perforated_block_regulation_config(
    resolution: int = 56,
    backend: BackendName = "auto",
    final_time: float = 0.24,
    insertion_start_time: float = 0.05,
    insertion_end_time: float = 0.12,
    insertion_fraction: float = 0.50,
    source_scale: float = 0.5,
    loss_scale: float = 120.0,
    thermal_exchange: float = 12.0,
    channel_counts: tuple[int, int] = (6, 4),
    *,
    parameters: PerforatedBlockParameters | None = None,
) -> RadiantWaveConfig:
    """Build the reusable perforated-block regulation precursor recipe.

    The returned configuration uses only explicit material fields, a geometric
    recipe, and generic scheduled events.  ``material_layout`` remains set for
    legacy plot selection, not for solver-side geometry construction.
    """
    parameters = parameters or PerforatedBlockParameters(
        resolution=resolution,
        backend=backend,
        final_time=final_time,
        insertion_start_time=insertion_start_time,
        insertion_end_time=insertion_end_time,
        insertion_fraction=insertion_fraction,
        source_scale=source_scale,
        loss_scale=loss_scale,
        thermal_exchange=thermal_exchange,
        channel_counts=channel_counts,
    )
    base = RadiantWaveConfig(
        dimensions=3,
        resolution=(parameters.resolution,) * 3,
        half_extent=parameters.half_extent,
    )
    loss_insert = replace(
        parameters.materials.loss_material.material_properties(),
        activity_diffusivity=0.18,
        thermal_conductivity=0.60,
        loss_rate=parameters.materials.loss_material.loss_rate * parameters.loss_scale,
        heat_loss_rate=(
            parameters.materials.loss_material.heat_loss_rate * parameters.loss_scale
        ),
        wave_damping=(
            parameters.materials.loss_material.wave_damping * parameters.loss_scale
        ),
    )
    active_medium = replace(
        parameters.materials.active_medium.material_properties(),
        activity_diffusivity=0.08,
        loss_rate=1.60,
        thermal_conductivity=0.08,
    )
    open_passage = replace(
        parameters.materials.open_passage.material_properties(),
        activity_diffusivity=0.16,
        thermal_conductivity=0.35,
    )
    coordinates = cell_centers(base)
    boundary, passages, insertion_rank = perforated_block_masks(
        cast(
            tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]],
            coordinates,
        ),
        base.half_extent,
        channel_counts=parameters.channel_counts,
        block_fraction=parameters.block_fraction,
        channel_radius_fraction=parameters.channel_radius_fraction,
    )
    initial_ids = np.where(boundary, REFLECTOR_ID, NEUTRAL_ID)
    initial_ids = np.where(passages, CHANNEL_ID, initial_ids).astype(
        np.int8,
        copy=False,
    )
    ramp = LinearRamp(
        parameters.insertion_start_time,
        parameters.insertion_end_time,
        parameters.insertion_fraction,
    )
    schedule = MaterialEventSchedule(
        replacements=(
            MaterialReplacementEvent(
                name="axial loss-material insertion",
                target_material_id=int(ABSORBER_ID),
                region=passages,
                rank=insertion_rank,
                ramp=ramp,
            ),
        ),
        property_ramps=(
            MaterialPropertyRamp(
                name="active-medium thermal exchange",
                property_name="heat_loss_rate",
                region=initial_ids == NEUTRAL_ID,
                amplitude=parameters.thermal_exchange,
                ramp=ramp,
            ),
        ),
    )
    return RadiantWaveConfig(
        dimensions=3,
        resolution=(parameters.resolution,) * 3,
        final_time=parameters.final_time,
        backend=parameters.backend,
        half_extent=parameters.half_extent,
        cfl=parameters.cfl,
        maximum_timestep=parameters.maximum_timestep,
        material_layout="channel-block",
        initial_material_ids=initial_ids,
        material_events=schedule,
        seed_width=parameters.source.seed_width,
        seed_amplitude=parameters.source.seed_amplitude,
        heat_source_rate=parameters.source.heat_source_rate * parameters.source_scale,
        heat_feedback=parameters.source.heat_feedback * parameters.source_scale,
        wave_source_rate=parameters.source.wave_source_rate * parameters.source_scale,
        wave_pressure_feedback=(
            parameters.source.wave_pressure_feedback * parameters.source_scale
        ),
        reflector=parameters.materials.reflector.material_properties(),
        absorber=loss_insert,
        neutral=active_medium,
        channel=open_passage,
    )
####


def open_shell_relaxation_config(
    resolution: int = 48,
    backend: BackendName = "auto",
    final_time: float = 0.06,
    insertion_time: float = 0.03,
    source_scale: float = 3.0,
    loss_scale: float = 12.0,
    *,
    parameters: ShellRelaxationParameters | None = None,
) -> RadiantWaveConfig:
    """Build a 3D source-dominated shell with a scheduled half-space loss event.

    This replaces the former named ``spherical-shell-open`` solver mode with
    explicit initial material IDs and a generic material replacement event.
    """
    parameters = parameters or ShellRelaxationParameters(
        resolution=resolution,
        backend=backend,
        final_time=final_time,
        insertion_time=insertion_time,
        source_scale=source_scale,
        loss_scale=loss_scale,
    )
    base = RadiantWaveConfig(
        dimensions=3,
        resolution=(parameters.resolution,) * 3,
        half_extent=parameters.half_extent,
    )
    coordinates = cast(
        tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]],
        cell_centers(base),
    )
    outer = spherical_shell_mask(
        coordinates,
        radius=parameters.shell_radius_fraction * base.half_extent,
    )
    initial_ids = np.where(outer, REFLECTOR_ID, NEUTRAL_ID).astype(np.int8, copy=False)
    right_half = axial_half_mask(coordinates)
    absorber = replace(
        parameters.materials.loss_material.material_properties(),
        loss_rate=parameters.materials.loss_material.loss_rate * parameters.loss_scale,
        heat_loss_rate=(
            parameters.materials.loss_material.heat_loss_rate * parameters.loss_scale
        ),
        wave_damping=(
            parameters.materials.loss_material.wave_damping * parameters.loss_scale
        ),
    )
    schedule = MaterialEventSchedule(
        replacements=(
            MaterialReplacementEvent(
                name="right-half loss-material insertion",
                target_material_id=int(ABSORBER_ID),
                region=(~outer) & right_half,
                rank=np.zeros_like(initial_ids, dtype=np.float64),
                ramp=LinearRamp(parameters.insertion_time, parameters.insertion_time, 1.0),
            ),
        )
    )
    return RadiantWaveConfig(
        dimensions=3,
        resolution=(parameters.resolution,) * 3,
        final_time=parameters.final_time,
        backend=parameters.backend,
        half_extent=parameters.half_extent,
        material_layout="spherical-shell-open",
        initial_material_ids=initial_ids,
        material_events=schedule,
        seed_width=parameters.source.seed_width,
        seed_amplitude=parameters.source.seed_amplitude,
        heat_source_rate=parameters.source.heat_source_rate * parameters.source_scale,
        heat_feedback=parameters.source.heat_feedback * parameters.source_scale,
        wave_source_rate=parameters.source.wave_source_rate * parameters.source_scale,
        wave_pressure_feedback=(
            parameters.source.wave_pressure_feedback * parameters.source_scale
        ),
        reflector=parameters.materials.reflector.material_properties(),
        neutral=parameters.materials.active_medium.material_properties(),
        absorber=absorber,
    )
####


def asymmetric_shell_config(
    resolution: int,
    backend: BackendName,
    final_time: float = 0.02,
) -> RadiantWaveConfig:
    """Build a generic heterogeneous spherical-shell recipe from explicit IDs."""
    base = RadiantWaveConfig(dimensions=3, resolution=(resolution,) * 3)
    coordinates = cast(
        tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]],
        cell_centers(base),
    )
    x, y, z = np.meshgrid(*coordinates, indexing="ij", sparse=True)
    shell = spherical_shell_mask(coordinates, radius=0.62 * base.half_extent)
    cap = shell & (x > 0.20 * base.half_extent) & (y > -0.25 * base.half_extent)
    inclusion_a = (x - 0.24 * base.half_extent) ** 2 + (
        y + 0.18 * base.half_extent
    ) ** 2 + (z - 0.10 * base.half_extent) ** 2 < (0.10 * base.half_extent) ** 2
    inclusion_b = (x + 0.22 * base.half_extent) ** 2 + (
        y - 0.20 * base.half_extent
    ) ** 2 + (z + 0.16 * base.half_extent) ** 2 < (0.08 * base.half_extent) ** 2
    initial_ids = np.where(shell, REFLECTOR_ID, NEUTRAL_ID)
    initial_ids = np.where(cap | inclusion_a | inclusion_b, ABSORBER_ID, initial_ids)
    return RadiantWaveConfig(
        dimensions=3,
        resolution=(resolution,) * 3,
        final_time=final_time,
        backend=backend,
        material_layout="spherical-shell",
        initial_material_ids=initial_ids.astype(np.int8, copy=False),
    )
####


def reactive_pressure_config(
    specific_heat: float = 2.5,
    gas_constant: float = 1.0,
    heat_release_per_mass: float = 0.75,
) -> ReactiveEulerConfig:
    """Return the normalized 1D pressure-driven demonstration parameters."""
    return ReactiveEulerConfig(
        gamma=1.0 + gas_constant / specific_heat,
        gas_constant=gas_constant,
        specific_heat=specific_heat,
        heat_release_per_mass=heat_release_per_mass,
    )
####


def phase_impulse_config(
    parameters: PhaseThermalParameters | None = None,
) -> PhaseEulerConfig:
    """Return the normalized feedback, EOS, and phase-transition parameters."""
    return (parameters or PhaseThermalParameters()).phase_config()
####
