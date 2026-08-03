from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

from converging_flow.backend import (
    Array,
    ArrayBackend,
    BackendName,
    ResolvedBackendName,
    get_array_backend,
)
from converging_flow.implicit import (
    DiffusionMethod,
    LinearSolverConfig,
    advance_diffusion,
)
from converging_flow.stencils import conservative_flux_divergence as _flux_divergence

RadiantDimension = Literal[1, 2, 3]
MaterialLayout = Literal["slab", "spherical-shell", "spherical-shell-open"]
FloatArray: TypeAlias = NDArray[np.float64]
IntegerArray: TypeAlias = NDArray[np.int8]

REFLECTOR_ID = np.int8(0)
NEUTRAL_ID = np.int8(1)
ABSORBER_ID = np.int8(2)


@dataclass(frozen=True, slots=True)
class MaterialProperties:
    """Dimensionless properties for one generic reactive wave material."""

    activity_diffusivity: float
    growth_rate: float
    loss_rate: float
    thermal_conductivity: float
    heat_capacity: float
    heat_loss_rate: float
    wave_density: float
    wave_stiffness: float
    wave_damping: float

    def __post_init__(self) -> None:
        values = (
            self.activity_diffusivity,
            self.growth_rate,
            self.loss_rate,
            self.thermal_conductivity,
            self.heat_capacity,
            self.heat_loss_rate,
            self.wave_density,
            self.wave_stiffness,
            self.wave_damping,
        )
        if any(value < 0.0 for value in values):
            raise ValueError("material properties cannot be negative")
        ####
        if self.heat_capacity <= 0.0:
            raise ValueError("heat_capacity must be positive")
        ####
        if self.wave_density <= 0.0:
            raise ValueError("wave_density must be positive")
        ####
        if self.wave_stiffness <= 0.0:
            raise ValueError("wave_stiffness must be positive")
        ####
    ####

    @property
    def wave_speed(self) -> float:
        return float(np.sqrt(self.wave_stiffness / self.wave_density))
    ####

    @property
    def wave_impedance(self) -> float:
        return float(np.sqrt(self.wave_density * self.wave_stiffness))
    ####
####


def default_reflector() -> MaterialProperties:
    """High-impedance, weakly damped material that reflects scalar waves."""
    base_stiffness = 0.65**2
    return MaterialProperties(
        activity_diffusivity=0.010,
        growth_rate=2.35,
        loss_rate=0.45,
        thermal_conductivity=0.018,
        heat_capacity=1.10,
        heat_loss_rate=0.75,
        wave_density=4.0,
        wave_stiffness=4.0 * base_stiffness,
        wave_damping=0.08,
    )
####

def default_neutral() -> MaterialProperties:
    """Reference material for the central transition slab."""
    return MaterialProperties(
        activity_diffusivity=0.012,
        growth_rate=2.20,
        loss_rate=0.55,
        thermal_conductivity=0.025,
        heat_capacity=1.00,
        heat_loss_rate=1.10,
        wave_density=1.0,
        wave_stiffness=0.65**2,
        wave_damping=0.20,
    )
####


def default_absorber() -> MaterialProperties:
    """Approximately impedance-matched, strongly damped wave absorber."""
    return MaterialProperties(
        activity_diffusivity=0.006,
        growth_rate=1.45,
        loss_rate=2.80,
        thermal_conductivity=0.040,
        heat_capacity=1.40,
        heat_loss_rate=2.20,
        wave_density=1.0,
        wave_stiffness=0.65**2,
        wave_damping=4.50,
    )
####


@dataclass(frozen=True, slots=True)
class RadiantWaveConfig:
    """Configuration for a heterogeneous autocatalytic scalar-wave demo.

    All values are normalized. The wave field is a generic scalar wave, not an
    electromagnetic or radiation-transport solution. ``wave_pressure_feedback``
    is therefore a phenomenological coupling, not a mechanical pressure law.

    ``backend`` selects NumPy CPU arrays, optional CuPy GPU arrays, or automatic
    device selection. ``diffusion_method`` controls only activity and heat
    diffusion; wave propagation remains explicitly CFL-limited.
    """

    dimensions: RadiantDimension
    resolution: tuple[int, ...]
    backend: BackendName = "numpy"
    diffusion_method: DiffusionMethod = "auto"
    material_layout: MaterialLayout = "slab"
    absorber_insertion_time: float | None = None
    implicit_switch_ratio: float = 0.25
    linear_solver: LinearSolverConfig = LinearSolverConfig()
    half_extent: float = 1.0
    final_time: float = 1.0
    max_steps: int = 100_000
    cfl: float = 0.30
    maximum_timestep: float = 2.0e-3
    neutral_half_width: float = 0.08
    seed_width: float = 0.10
    seed_amplitude: float = 0.85
    heat_source_rate: float = 1.50
    heat_feedback: float = 0.25
    wave_source_rate: float = 0.90
    wave_pressure_feedback: float = 0.08
    reflector: MaterialProperties = default_reflector()
    neutral: MaterialProperties = default_neutral()
    absorber: MaterialProperties = default_absorber()

    def __post_init__(self) -> None:
        if self.dimensions not in (1, 2, 3):
            raise ValueError("dimensions must be 1, 2, or 3")
        ####
        if len(self.resolution) != self.dimensions:
            raise ValueError("resolution length must match dimensions")
        ####
        if any(size < 8 for size in self.resolution):
            raise ValueError("each resolution entry must be at least 8")
        ####
        if self.backend not in ("auto", "numpy", "cupy"):
            raise ValueError("backend must be 'auto', 'numpy', or 'cupy'")
        ####
        if self.diffusion_method not in ("auto", "explicit", "crank-nicolson"):
            raise ValueError(
                "diffusion_method must be 'auto', 'explicit', or "
                "'crank-nicolson'"
            )
        ####
        if self.material_layout not in (
            "slab",
            "spherical-shell",
            "spherical-shell-open",
        ):
            raise ValueError(
                "material_layout must be 'slab', 'spherical-shell', "
                "or 'spherical-shell-open'"
            )
        ####
        if self.material_layout != "slab" and self.dimensions != 3:
            raise ValueError("spherical-shell material layout requires 3D")
        ####
        if self.absorber_insertion_time is not None and not (
            0.0 < self.absorber_insertion_time < self.final_time
        ):
            raise ValueError(
                "absorber_insertion_time must lie strictly inside the run"
            )
        ####
        if not 0.0 < self.implicit_switch_ratio <= 1.0:
            raise ValueError("implicit_switch_ratio must lie in (0, 1]")
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
        if not 0.0 <= self.neutral_half_width < self.half_extent:
            raise ValueError("neutral_half_width must lie inside the domain")
        ####
        if self.seed_width <= 0.0:
            raise ValueError("seed_width must be positive")
        ####
        if not 0.0 <= self.seed_amplitude <= 1.0:
            raise ValueError("seed_amplitude must lie between zero and one")
        ####
        rates = (
            self.heat_source_rate,
            self.heat_feedback,
            self.wave_source_rate,
            self.wave_pressure_feedback,
        )
        if any(rate < 0.0 for rate in rates):
            raise ValueError("source and feedback rates cannot be negative")
        ####
    ####

    @property
    def spacing(self) -> tuple[float, ...]:
        return tuple(2.0 * self.half_extent / size for size in self.resolution)
    ####
####


@dataclass(frozen=True, slots=True)
class MaterialFields:
    material_id: IntegerArray
    activity_diffusivity: FloatArray
    growth_rate: FloatArray
    loss_rate: FloatArray
    thermal_conductivity: FloatArray
    heat_capacity: FloatArray
    heat_loss_rate: FloatArray
    wave_density: FloatArray
    wave_stiffness: FloatArray
    wave_damping: FloatArray
####


@dataclass(frozen=True, slots=True)
class DeviceMaterialFields:
    material_id: Array
    activity_diffusivity: Array
    growth_rate: Array
    loss_rate: Array
    thermal_conductivity: Array
    heat_capacity: Array
    heat_loss_rate: Array
    wave_density: Array
    wave_stiffness: Array
    wave_damping: Array
####


@dataclass(frozen=True, slots=True)
class RadiantWaveDiagnostics:
    time: float
    step: int
    total_activity: float
    maximum_activity: float
    maximum_heat: float
    wave_rms: float
    total_wave_energy: float
    maximum_wave_pressure: float
    maximum_force_magnitude: float
####


@dataclass(frozen=True, slots=True)
class RadiantWaveBudget:
    """Integrated normalized state, transfer rates, and balance diagnostic."""

    total_activity: float
    autocatalytic_activity_rate: float
    thermal_feedback_activity_rate: float
    wave_feedback_activity_rate: float
    activity_loss_rate: float
    thermal_energy: float
    heat_source_power: float
    heat_loss_power: float
    total_wave_energy: float
    wave_source_power: float
    wave_dissipation_power: float
    source_strength: float
    sink_strength: float
    balance_factor: float
    material_wave_energy: tuple[float, float, float]
    material_wave_dissipation_power: tuple[float, float, float]
####


@dataclass(frozen=True, slots=True)
class RadiantWaveFrame:
    time: float
    activity: FloatArray
    heat: FloatArray
    wave: FloatArray
    wave_velocity: FloatArray
    wave_energy: FloatArray
    wave_pressure: FloatArray
    material_id: IntegerArray
    absorber_inserted: bool
    budget: RadiantWaveBudget
####


@dataclass(frozen=True, slots=True)
class RadiantWaveResult:
    config: RadiantWaveConfig
    resolved_backend: ResolvedBackendName
    resolved_diffusion_method: Literal["explicit", "crank-nicolson"]
    coordinates: tuple[FloatArray, ...]
    materials: MaterialFields
    activity: FloatArray
    heat: FloatArray
    wave: FloatArray
    wave_velocity: FloatArray
    wave_energy: FloatArray
    wave_pressure: FloatArray
    force_magnitude: FloatArray
    time: float
    steps: int
    initial_diagnostics: RadiantWaveDiagnostics
    final_diagnostics: RadiantWaveDiagnostics
    absorber_inserted: bool = False
    frames: tuple[RadiantWaveFrame, ...] = ()
####


def cell_centers(config: RadiantWaveConfig) -> tuple[FloatArray, ...]:
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


def material_ids(
    coordinates: tuple[FloatArray, ...],
    config: RadiantWaveConfig,
) -> IntegerArray:
    """Return material IDs for the configured slab or spherical layout."""
    if config.material_layout != "slab":
        radius = _radius_field(coordinates, config.resolution)
        mesh = np.meshgrid(*coordinates, indexing="ij", sparse=True)
        shell = radius >= 0.62 * config.half_extent
        ids = np.where(shell, REFLECTOR_ID, NEUTRAL_ID).astype(np.int8)

        if config.material_layout == "spherical-shell-open":
            return ids

        # A broad +x cap makes the shell intentionally asymmetric. Two small
        # absorbing inclusions provide additional generic scattering/loss
        # features inside the active interior.
        x, y, z = mesh
        cap = shell & (x > 0.20 * config.half_extent) & (y > -0.25 * config.half_extent)
        inclusion_a = (
            (x - 0.24 * config.half_extent) ** 2
            + (y + 0.18 * config.half_extent) ** 2
            + (z - 0.10 * config.half_extent) ** 2
            < (0.10 * config.half_extent) ** 2
        )
        inclusion_b = (
            (x + 0.22 * config.half_extent) ** 2
            + (y - 0.20 * config.half_extent) ** 2
            + (z + 0.16 * config.half_extent) ** 2
            < (0.08 * config.half_extent) ** 2
        )
        return np.where(cap | inclusion_a | inclusion_b, ABSORBER_ID, ids).astype(
            np.int8,
            copy=False,
        )

    first_coordinate = coordinates[0]
    shape = (first_coordinate.size,) + (1,) * (config.dimensions - 1)
    x = first_coordinate.reshape(shape)
    ids = np.full(config.resolution, NEUTRAL_ID, dtype=np.int8)
    ids[...] = np.where(
        x < -config.neutral_half_width,
        REFLECTOR_ID,
        np.where(x > config.neutral_half_width, ABSORBER_ID, NEUTRAL_ID),
    )
    return ids
####


def _property_field(
    ids: IntegerArray,
    reflector_value: float,
    neutral_value: float,
    absorber_value: float,
) -> FloatArray:
    return np.choose(
        ids,
        (reflector_value, neutral_value, absorber_value),
    ).astype(np.float64, copy=False)
####


def build_material_fields(
    ids: IntegerArray,
    config: RadiantWaveConfig,
) -> MaterialFields:
    reflector = config.reflector
    neutral = config.neutral
    absorber = config.absorber
    return MaterialFields(
        material_id=ids,
        activity_diffusivity=_property_field(
            ids,
            reflector.activity_diffusivity,
            neutral.activity_diffusivity,
            absorber.activity_diffusivity,
        ),
        growth_rate=_property_field(
            ids,
            reflector.growth_rate,
            neutral.growth_rate,
            absorber.growth_rate,
        ),
        loss_rate=_property_field(
            ids,
            reflector.loss_rate,
            neutral.loss_rate,
            absorber.loss_rate,
        ),
        thermal_conductivity=_property_field(
            ids,
            reflector.thermal_conductivity,
            neutral.thermal_conductivity,
            absorber.thermal_conductivity,
        ),
        heat_capacity=_property_field(
            ids,
            reflector.heat_capacity,
            neutral.heat_capacity,
            absorber.heat_capacity,
        ),
        heat_loss_rate=_property_field(
            ids,
            reflector.heat_loss_rate,
            neutral.heat_loss_rate,
            absorber.heat_loss_rate,
        ),
        wave_density=_property_field(
            ids,
            reflector.wave_density,
            neutral.wave_density,
            absorber.wave_density,
        ),
        wave_stiffness=_property_field(
            ids,
            reflector.wave_stiffness,
            neutral.wave_stiffness,
            absorber.wave_stiffness,
        ),
        wave_damping=_property_field(
            ids,
            reflector.wave_damping,
            neutral.wave_damping,
            absorber.wave_damping,
        ),
    )
####


def _device_material_fields(
    materials: MaterialFields,
    backend: ArrayBackend,
) -> DeviceMaterialFields:
    return DeviceMaterialFields(
        material_id=backend.asarray(materials.material_id, dtype=np.int8),
        activity_diffusivity=backend.asarray(materials.activity_diffusivity),
        growth_rate=backend.asarray(materials.growth_rate),
        loss_rate=backend.asarray(materials.loss_rate),
        thermal_conductivity=backend.asarray(materials.thermal_conductivity),
        heat_capacity=backend.asarray(materials.heat_capacity),
        heat_loss_rate=backend.asarray(materials.heat_loss_rate),
        wave_density=backend.asarray(materials.wave_density),
        wave_stiffness=backend.asarray(materials.wave_stiffness),
        wave_damping=backend.asarray(materials.wave_damping),
    )
####


def initialize_fields(
    config: RadiantWaveConfig,
) -> tuple[
    tuple[FloatArray, ...],
    MaterialFields,
    FloatArray,
    FloatArray,
    FloatArray,
    FloatArray,
]:
    coordinates = cell_centers(config)
    radius = _radius_field(coordinates, config.resolution)
    ids = material_ids(coordinates, config)
    materials = build_material_fields(ids, config)
    activity = config.seed_amplitude * np.exp(
        -0.5 * (radius / config.seed_width) ** 2
    )
    heat = np.zeros(config.resolution, dtype=np.float64)
    wave = np.zeros(config.resolution, dtype=np.float64)
    wave_velocity = np.zeros(config.resolution, dtype=np.float64)
    return coordinates, materials, activity, heat, wave, wave_velocity
####


def conservative_flux_divergence(
    values: FloatArray,
    coefficient: FloatArray,
    spacing: tuple[float, ...],
) -> FloatArray:
    """NumPy reference wrapper for the portable conservative operator."""
    backend = get_array_backend("numpy")
    return cast(
        FloatArray,
        _flux_divergence(values, coefficient, spacing, backend),
    )
####


def _wave_energy_components_backend(
    wave: Array,
    wave_velocity: Array,
    materials: DeviceMaterialFields,
    spacing: tuple[float, ...],
    backend: ArrayBackend,
) -> tuple[Array, Array]:
    gradient_squared = backend.xp.zeros_like(wave)
    gradients = backend.xp.gradient(wave, *spacing, edge_order=1)
    if wave.ndim == 1:
        gradients = (gradients,)
    ####
    for gradient in gradients:
        gradient_squared += gradient * gradient
    ####
    kinetic = 0.5 * (
        materials.wave_density * wave_velocity * wave_velocity
    )
    strain = 0.5 * materials.wave_stiffness * gradient_squared
    return kinetic, strain
####


def _wave_energy_density_backend(
    wave: Array,
    wave_velocity: Array,
    materials: DeviceMaterialFields,
    spacing: tuple[float, ...],
    backend: ArrayBackend,
) -> Array:
    kinetic, strain = _wave_energy_components_backend(
        wave,
        wave_velocity,
        materials,
        spacing,
        backend,
    )
    return kinetic + strain
####


def wave_energy_density(
    wave: FloatArray,
    wave_velocity: FloatArray,
    materials: MaterialFields,
    spacing: tuple[float, ...],
) -> FloatArray:
    backend = get_array_backend("numpy")
    device_materials = _device_material_fields(materials, backend)
    return cast(
        FloatArray,
        _wave_energy_density_backend(
            wave,
            wave_velocity,
            device_materials,
            spacing,
            backend,
        ),
    )
####


def wave_energy_components(
    wave: FloatArray,
    wave_velocity: FloatArray,
    materials: MaterialFields,
    spacing: tuple[float, ...],
) -> tuple[FloatArray, FloatArray]:
    """Return kinetic and strain components of scalar-wave energy density."""
    backend = get_array_backend("numpy")
    device_materials = _device_material_fields(materials, backend)
    kinetic, strain = _wave_energy_components_backend(
        wave,
        wave_velocity,
        device_materials,
        spacing,
        backend,
    )
    return cast(FloatArray, kinetic), cast(FloatArray, strain)
####


def _pressure_and_force_backend(
    wave_energy: Array,
    spacing: tuple[float, ...],
    backend: ArrayBackend,
) -> tuple[Array, Array]:
    pressure = wave_energy / float(wave_energy.ndim)
    gradients = backend.xp.gradient(pressure, *spacing, edge_order=1)
    if pressure.ndim == 1:
        gradients = (gradients,)
    ####
    magnitude_squared = backend.xp.zeros_like(pressure)
    for gradient in gradients:
        magnitude_squared += gradient * gradient
    ####
    return pressure, backend.xp.sqrt(magnitude_squared)
####


def pressure_and_force(
    wave_energy: FloatArray,
    spacing: tuple[float, ...],
) -> tuple[FloatArray, FloatArray]:
    backend = get_array_backend("numpy")
    pressure, force = _pressure_and_force_backend(
        wave_energy,
        spacing,
        backend,
    )
    return cast(FloatArray, pressure), cast(FloatArray, force)
####


def _integral_backend(
    values: Array,
    cell_volume: float,
    backend: ArrayBackend,
) -> float:
    return backend.scalar(backend.xp.sum(values)) * cell_volume
####


def _budget_backend(
    activity: Array,
    heat: Array,
    wave_velocity: Array,
    wave_energy: Array,
    wave_pressure: Array,
    materials: DeviceMaterialFields,
    config: RadiantWaveConfig,
    backend: ArrayBackend,
) -> RadiantWaveBudget:
    cell_volume = float(np.prod(config.spacing))
    saturation = backend.xp.maximum(1.0 - activity, 0.0)
    autocatalytic_rate = materials.growth_rate * activity * saturation
    thermal_feedback_rate = config.heat_feedback * heat * saturation
    wave_feedback_rate = (
        config.wave_pressure_feedback * wave_pressure * saturation
    )
    activity_loss_rate = materials.loss_rate * activity

    thermal_energy_density = materials.heat_capacity * heat
    heat_source_density = config.heat_source_rate * activity
    heat_loss_density = materials.heat_loss_rate * heat

    wave_source_power_density = (
        config.wave_source_rate * activity * wave_velocity
    )
    wave_dissipation_density = (
        materials.wave_density
        * materials.wave_damping
        * wave_velocity
        * wave_velocity
    )

    material_wave_energy: list[float] = []
    material_wave_dissipation: list[float] = []
    for material_identifier in (REFLECTOR_ID, NEUTRAL_ID, ABSORBER_ID):
        mask = materials.material_id == material_identifier
        material_wave_energy.append(
            _integral_backend(
                backend.xp.where(mask, wave_energy, 0.0),
                cell_volume,
                backend,
            )
        )
        material_wave_dissipation.append(
            _integral_backend(
                backend.xp.where(mask, wave_dissipation_density, 0.0),
                cell_volume,
                backend,
            )
        )
    ####

    total_activity = _integral_backend(activity, cell_volume, backend)
    autocatalytic_activity_rate = _integral_backend(
        autocatalytic_rate,
        cell_volume,
        backend,
    )
    thermal_feedback_activity_rate = _integral_backend(
        thermal_feedback_rate,
        cell_volume,
        backend,
    )
    wave_feedback_activity_rate = _integral_backend(
        wave_feedback_rate,
        cell_volume,
        backend,
    )
    activity_loss_rate = _integral_backend(
        activity_loss_rate,
        cell_volume,
        backend,
    )
    thermal_energy = _integral_backend(
        thermal_energy_density,
        cell_volume,
        backend,
    )
    heat_source_power = _integral_backend(
        heat_source_density,
        cell_volume,
        backend,
    )
    heat_loss_power = _integral_backend(
        heat_loss_density,
        cell_volume,
        backend,
    )
    total_wave_energy = _integral_backend(
        wave_energy,
        cell_volume,
        backend,
    )
    wave_source_power = _integral_backend(
        wave_source_power_density,
        cell_volume,
        backend,
    )
    wave_dissipation_power = _integral_backend(
        wave_dissipation_density,
        cell_volume,
        backend,
    )
    source_strength = (
        autocatalytic_activity_rate
        + thermal_feedback_activity_rate
        + wave_feedback_activity_rate
        + heat_source_power
        + max(wave_source_power, 0.0)
    )
    sink_strength = (
        activity_loss_rate
        + heat_loss_power
        + wave_dissipation_power
    )
    balance_factor = source_strength / max(sink_strength, np.finfo(float).tiny)

    return RadiantWaveBudget(
        total_activity=total_activity,
        autocatalytic_activity_rate=autocatalytic_activity_rate,
        thermal_feedback_activity_rate=thermal_feedback_activity_rate,
        wave_feedback_activity_rate=wave_feedback_activity_rate,
        activity_loss_rate=activity_loss_rate,
        thermal_energy=thermal_energy,
        heat_source_power=heat_source_power,
        heat_loss_power=heat_loss_power,
        total_wave_energy=total_wave_energy,
        wave_source_power=wave_source_power,
        wave_dissipation_power=wave_dissipation_power,
        source_strength=source_strength,
        sink_strength=sink_strength,
        balance_factor=balance_factor,
        material_wave_energy=cast(
            tuple[float, float, float],
            tuple(material_wave_energy),
        ),
        material_wave_dissipation_power=cast(
            tuple[float, float, float],
            tuple(material_wave_dissipation),
        ),
    )
####


def radiant_wave_budget(
    activity: FloatArray,
    heat: FloatArray,
    wave_velocity: FloatArray,
    wave_energy: FloatArray,
    wave_pressure: FloatArray,
    materials: MaterialFields,
    config: RadiantWaveConfig,
) -> RadiantWaveBudget:
    """Return integrated normalized state and transfer rates."""
    backend = get_array_backend("numpy")
    return _budget_backend(
        activity,
        heat,
        wave_velocity,
        wave_energy,
        wave_pressure,
        _device_material_fields(materials, backend),
        config,
        backend,
    )
####


def interface_reflection_coefficient(
    left: MaterialProperties,
    right: MaterialProperties,
) -> float:
    """Normal-incidence scalar-wave amplitude reflection coefficient."""
    left_impedance = left.wave_impedance
    right_impedance = right.wave_impedance
    return (right_impedance - left_impedance) / (
        right_impedance + left_impedance
    )
####


def _local_wave_right_hand_side(
    activity: Array,
    heat: Array,
    wave: Array,
    wave_velocity: Array,
    materials: DeviceMaterialFields,
    config: RadiantWaveConfig,
    backend: ArrayBackend,
) -> tuple[Array, Array, Array, Array]:
    wave_restoring = _flux_divergence(
        wave,
        materials.wave_stiffness,
        config.spacing,
        backend,
    )
    energy = _wave_energy_density_backend(
        wave,
        wave_velocity,
        materials,
        config.spacing,
        backend,
    )
    pressure, _force_magnitude = _pressure_and_force_backend(
        energy,
        config.spacing,
        backend,
    )
    saturation = backend.xp.maximum(1.0 - activity, 0.0)

    activity_rate = (
        materials.growth_rate * activity * saturation
        - materials.loss_rate * activity
        + config.heat_feedback * heat * saturation
        + config.wave_pressure_feedback * pressure * saturation
    )
    heat_rate = (
        config.heat_source_rate * activity - materials.heat_loss_rate * heat
    ) / materials.heat_capacity
    wave_rate = wave_velocity
    wave_velocity_rate = (
        wave_restoring + config.wave_source_rate * activity
    ) / materials.wave_density - materials.wave_damping * wave_velocity
    return activity_rate, heat_rate, wave_rate, wave_velocity_rate
####


def _advance_local_wave_midpoint(
    activity: Array,
    heat: Array,
    wave: Array,
    wave_velocity: Array,
    materials: DeviceMaterialFields,
    config: RadiantWaveConfig,
    timestep: float,
    backend: ArrayBackend,
) -> tuple[Array, Array, Array, Array]:
    first_rate = _local_wave_right_hand_side(
        activity,
        heat,
        wave,
        wave_velocity,
        materials,
        config,
        backend,
    )
    midpoint_activity = backend.xp.clip(
        activity + 0.5 * timestep * first_rate[0],
        0.0,
        1.0,
    )
    midpoint_heat = backend.xp.maximum(
        heat + 0.5 * timestep * first_rate[1],
        0.0,
    )
    midpoint_wave = wave + 0.5 * timestep * first_rate[2]
    midpoint_velocity = wave_velocity + 0.5 * timestep * first_rate[3]

    second_rate = _local_wave_right_hand_side(
        midpoint_activity,
        midpoint_heat,
        midpoint_wave,
        midpoint_velocity,
        materials,
        config,
        backend,
    )
    return (
        backend.xp.clip(activity + timestep * second_rate[0], 0.0, 1.0),
        backend.xp.maximum(heat + timestep * second_rate[1], 0.0),
        wave + timestep * second_rate[2],
        wave_velocity + timestep * second_rate[3],
    )
####


def _advance_fields_backend(
    activity: Array,
    heat: Array,
    wave: Array,
    wave_velocity: Array,
    materials: DeviceMaterialFields,
    config: RadiantWaveConfig,
    timestep: float,
    backend: ArrayBackend,
    diffusion_method: Literal["explicit", "crank-nicolson"],
) -> tuple[Array, Array, Array, Array]:
    """Advance with Strang splitting and selectable diffusion integration."""
    if timestep <= 0.0:
        raise ValueError("timestep must be positive")
    ####

    half_timestep = 0.5 * timestep
    activity, heat, wave, wave_velocity = _advance_local_wave_midpoint(
        activity,
        heat,
        wave,
        wave_velocity,
        materials,
        config,
        half_timestep,
        backend,
    )

    activity = advance_diffusion(
        activity,
        materials.activity_diffusivity,
        config.spacing,
        timestep,
        backend,
        diffusion_method,
        config.linear_solver,
    )
    heat = advance_diffusion(
        heat,
        materials.thermal_conductivity,
        config.spacing,
        timestep,
        backend,
        diffusion_method,
        config.linear_solver,
        capacity=materials.heat_capacity,
    )
    activity = backend.xp.clip(activity, 0.0, 1.0)
    heat = backend.xp.maximum(heat, 0.0)

    return _advance_local_wave_midpoint(
        activity,
        heat,
        wave,
        wave_velocity,
        materials,
        config,
        half_timestep,
        backend,
    )
####


def advance_fields(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    materials: MaterialFields,
    config: RadiantWaveConfig,
    timestep: float,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Portable one-step API that returns NumPy arrays for callers and tests."""
    backend = get_array_backend(config.backend)
    device_materials = _device_material_fields(materials, backend)
    diffusion_method = resolve_diffusion_method(config, materials)
    result = _advance_fields_backend(
        backend.asarray(activity),
        backend.asarray(heat),
        backend.asarray(wave),
        backend.asarray(wave_velocity),
        device_materials,
        config,
        timestep,
        backend,
        diffusion_method,
    )
    return tuple(backend.to_numpy(field) for field in result)  # type: ignore[return-value]
####


def _timestep_limits(
    config: RadiantWaveConfig,
    materials: MaterialFields,
) -> tuple[float, float, float]:
    minimum_spacing = min(config.spacing)
    dimensionality = float(config.dimensions)

    maximum_activity_diffusivity = float(
        np.max(materials.activity_diffusivity)
    )
    maximum_thermal_diffusivity = float(
        np.max(materials.thermal_conductivity / materials.heat_capacity)
    )
    maximum_diffusivity = max(
        maximum_activity_diffusivity,
        maximum_thermal_diffusivity,
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

    maximum_wave_speed = float(
        np.max(np.sqrt(materials.wave_stiffness / materials.wave_density))
    )
    wave_limit = np.inf
    if maximum_wave_speed > 0.0:
        wave_limit = (
            config.cfl
            * minimum_spacing
            / (maximum_wave_speed * np.sqrt(dimensionality))
        )
    ####

    local_rate = float(
        np.max(
            materials.growth_rate
            + materials.loss_rate
            + materials.heat_loss_rate / materials.heat_capacity
            + materials.wave_damping
        )
    )
    reaction_limit = np.inf
    if local_rate > 0.0:
        reaction_limit = config.cfl / local_rate
    ####
    return float(diffusion_limit), float(wave_limit), float(reaction_limit)
####


def resolve_diffusion_method(
    config: RadiantWaveConfig,
    materials: MaterialFields,
) -> Literal["explicit", "crank-nicolson"]:
    if config.diffusion_method == "explicit":
        return "explicit"
    ####
    if config.diffusion_method == "crank-nicolson":
        return "crank-nicolson"
    ####

    diffusion_limit, wave_limit, reaction_limit = _timestep_limits(
        config,
        materials,
    )
    non_diffusion_limit = min(
        config.maximum_timestep,
        wave_limit,
        reaction_limit,
    )
    if diffusion_limit < config.implicit_switch_ratio * non_diffusion_limit:
        return "crank-nicolson"
    ####
    return "explicit"
####


def stable_timestep(
    config: RadiantWaveConfig,
    materials: MaterialFields,
    diffusion_method: Literal["explicit", "crank-nicolson"] | None = None,
) -> float:
    resolved_method = (
        resolve_diffusion_method(config, materials)
        if diffusion_method is None
        else diffusion_method
    )
    diffusion_limit, wave_limit, reaction_limit = _timestep_limits(
        config,
        materials,
    )
    if resolved_method == "crank-nicolson":
        diffusion_limit = np.inf
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

def _visualization_field(values: FloatArray) -> FloatArray:
    if values.ndim < 3:
        return values.copy()
    ####
    return values[:, :, values.shape[2] // 2].copy()
####


def _make_frame_backend(
    time: float,
    activity: Array,
    heat: Array,
    wave: Array,
    wave_velocity: Array,
    wave_energy: Array,
    wave_pressure: Array,
    materials: DeviceMaterialFields,
    absorber_inserted: bool,
    budget: RadiantWaveBudget,
    backend: ArrayBackend,
) -> RadiantWaveFrame:
    return RadiantWaveFrame(
        time=time,
        activity=_visualization_field(backend.to_numpy(activity)),
        heat=_visualization_field(backend.to_numpy(heat)),
        wave=_visualization_field(backend.to_numpy(wave)),
        wave_velocity=_visualization_field(
            backend.to_numpy(wave_velocity)
        ),
        wave_energy=_visualization_field(backend.to_numpy(wave_energy)),
        wave_pressure=_visualization_field(backend.to_numpy(wave_pressure)),
        material_id=backend.to_numpy(materials.material_id).astype(
            np.int8,
            copy=False,
        ),
        absorber_inserted=absorber_inserted,
        budget=budget,
    )
####


def _diagnostics_backend(
    activity: Array,
    heat: Array,
    wave: Array,
    wave_velocity: Array,
    materials: DeviceMaterialFields,
    config: RadiantWaveConfig,
    time: float,
    step: int,
    backend: ArrayBackend,
) -> RadiantWaveDiagnostics:
    energy = _wave_energy_density_backend(
        wave,
        wave_velocity,
        materials,
        config.spacing,
        backend,
    )
    pressure, force = _pressure_and_force_backend(
        energy,
        config.spacing,
        backend,
    )
    cell_volume = float(np.prod(config.spacing))
    return RadiantWaveDiagnostics(
        time=time,
        step=step,
        total_activity=backend.scalar(backend.xp.sum(activity)) * cell_volume,
        maximum_activity=backend.scalar(backend.xp.max(activity)),
        maximum_heat=backend.scalar(backend.xp.max(heat)),
        wave_rms=backend.scalar(backend.xp.sqrt(backend.xp.mean(wave * wave))),
        total_wave_energy=backend.scalar(backend.xp.sum(energy)) * cell_volume,
        maximum_wave_pressure=backend.scalar(backend.xp.max(pressure)),
        maximum_force_magnitude=backend.scalar(backend.xp.max(force)),
    )
####


def _absorber_insertion_mask(
    coordinates: tuple[FloatArray, ...],
    config: RadiantWaveConfig,
) -> IntegerArray:
    """Return a right-side generic absorber insertion region."""
    x = coordinates[0].reshape((config.resolution[0], 1, 1))
    mask = x > 0.20 * config.half_extent
    return np.broadcast_to(mask, config.resolution).copy()
####


def _insert_absorber_region(
    materials: DeviceMaterialFields,
    mask: Array,
    config: RadiantWaveConfig,
    backend: ArrayBackend,
) -> DeviceMaterialFields:
    """Replace a region with the configured generic absorber material."""
    absorber = config.absorber
    xp = backend.xp

    def replace(values: Array, value: float) -> Array:
        return xp.where(mask, value, values)
    ####

    return DeviceMaterialFields(
        material_id=backend.asarray(
            xp.where(mask, ABSORBER_ID, materials.material_id),
            dtype=np.int8,
        ),
        activity_diffusivity=replace(
            materials.activity_diffusivity,
            absorber.activity_diffusivity,
        ),
        growth_rate=replace(materials.growth_rate, absorber.growth_rate),
        loss_rate=replace(materials.loss_rate, absorber.loss_rate),
        thermal_conductivity=replace(
            materials.thermal_conductivity,
            absorber.thermal_conductivity,
        ),
        heat_capacity=replace(materials.heat_capacity, absorber.heat_capacity),
        heat_loss_rate=replace(materials.heat_loss_rate, absorber.heat_loss_rate),
        wave_density=replace(materials.wave_density, absorber.wave_density),
        wave_stiffness=replace(materials.wave_stiffness, absorber.wave_stiffness),
        wave_damping=replace(materials.wave_damping, absorber.wave_damping),
    )
####


def diagnostics(
    activity: FloatArray,
    heat: FloatArray,
    wave: FloatArray,
    wave_velocity: FloatArray,
    materials: MaterialFields,
    config: RadiantWaveConfig,
    time: float,
    step: int,
) -> RadiantWaveDiagnostics:
    backend = get_array_backend("numpy")
    return _diagnostics_backend(
        activity,
        heat,
        wave,
        wave_velocity,
        _device_material_fields(materials, backend),
        config,
        time,
        step,
        backend,
    )
####


def run_radiant_wave(
    config: RadiantWaveConfig,
    snapshot_count: int = 0,
) -> RadiantWaveResult:
    if snapshot_count == 1 or snapshot_count < 0:
        raise ValueError("snapshot_count must be zero or at least two")
    ####

    (
        coordinates,
        materials,
        activity_numpy,
        heat_numpy,
        wave_numpy,
        wave_velocity_numpy,
    ) = initialize_fields(config)
    backend = get_array_backend(config.backend)
    device_materials = _device_material_fields(materials, backend)
    absorber_inserted = False
    activity = backend.asarray(activity_numpy)
    heat = backend.asarray(heat_numpy)
    wave = backend.asarray(wave_numpy)
    wave_velocity = backend.asarray(wave_velocity_numpy)

    time = 0.0
    step = 0
    initial_diagnostics = _diagnostics_backend(
        activity,
        heat,
        wave,
        wave_velocity,
        device_materials,
        config,
        time,
        step,
        backend,
    )

    initial_energy = _wave_energy_density_backend(
        wave,
        wave_velocity,
        device_materials,
        config.spacing,
        backend,
    )
    initial_pressure, _initial_force = _pressure_and_force_backend(
        initial_energy,
        config.spacing,
        backend,
    )
    frames: list[RadiantWaveFrame] = []
    target_times = np.empty(0, dtype=np.float64)
    next_target = 0
    if snapshot_count >= 2:
        target_times = np.linspace(0.0, config.final_time, snapshot_count)
        initial_budget = _budget_backend(
            activity,
            heat,
            wave_velocity,
            initial_energy,
            initial_pressure,
            device_materials,
            config,
            backend,
        )
        frames.append(
            _make_frame_backend(
                time,
                activity,
                heat,
                wave,
                wave_velocity,
                initial_energy,
                initial_pressure,
                device_materials,
                absorber_inserted,
                initial_budget,
                backend,
            )
        )
        next_target = 1
    ####

    resolved_diffusion_method = resolve_diffusion_method(config, materials)
    base_timestep = stable_timestep(
        config,
        materials,
        resolved_diffusion_method,
    )
    while time < config.final_time and step < config.max_steps:
        timestep = min(base_timestep, config.final_time - time)
        if (
            config.absorber_insertion_time is not None
            and not absorber_inserted
        ):
            timestep = min(
                timestep,
                config.absorber_insertion_time - time,
            )
        activity, heat, wave, wave_velocity = _advance_fields_backend(
            activity,
            heat,
            wave,
            wave_velocity,
            device_materials,
            config,
            timestep,
            backend,
            resolved_diffusion_method,
        )
        time += timestep
        step += 1

        if (
            config.absorber_insertion_time is not None
            and not absorber_inserted
            and time >= config.absorber_insertion_time - 1.0e-14
        ):
            insertion_mask = _absorber_insertion_mask(coordinates, config)
            device_materials = _insert_absorber_region(
                device_materials,
                backend.asarray(insertion_mask),
                config,
                backend,
            )
            absorber_inserted = True

        while (
            next_target < snapshot_count
            and time >= target_times[next_target] - 1.0e-14
        ):
            frame_energy = _wave_energy_density_backend(
                wave,
                wave_velocity,
                device_materials,
                config.spacing,
                backend,
            )
            frame_pressure, _frame_force = _pressure_and_force_backend(
                frame_energy,
                config.spacing,
                backend,
            )
            frame_budget = _budget_backend(
                activity,
                heat,
                wave_velocity,
                frame_energy,
                frame_pressure,
                device_materials,
                config,
                backend,
            )
            frames.append(
                _make_frame_backend(
                    time,
                    activity,
                    heat,
                    wave,
                    wave_velocity,
                    frame_energy,
                    frame_pressure,
                    device_materials,
                    absorber_inserted,
                    frame_budget,
                    backend,
                )
            )
            next_target += 1
        ####
    ####

    if time < config.final_time:
        raise RuntimeError(
            f"maximum step count reached at t={time:.6g}, "
            f"target={config.final_time:.6g}"
        )
    ####

    energy = _wave_energy_density_backend(
        wave,
        wave_velocity,
        device_materials,
        config.spacing,
        backend,
    )
    pressure, force = _pressure_and_force_backend(
        energy,
        config.spacing,
        backend,
    )
    final_diagnostics = _diagnostics_backend(
        activity,
        heat,
        wave,
        wave_velocity,
        device_materials,
        config,
        time,
        step,
        backend,
    )
    backend.synchronize()
    final_materials = build_material_fields(
        backend.to_numpy(device_materials.material_id).astype(
            np.int8,
            copy=False,
        ),
        config,
    )
    return RadiantWaveResult(
        config=config,
        resolved_backend=backend.name,
        resolved_diffusion_method=resolved_diffusion_method,
        coordinates=coordinates,
        materials=final_materials,
        activity=backend.to_numpy(activity),
        heat=backend.to_numpy(heat),
        wave=backend.to_numpy(wave),
        wave_velocity=backend.to_numpy(wave_velocity),
        wave_energy=backend.to_numpy(energy),
        wave_pressure=backend.to_numpy(pressure),
        force_magnitude=backend.to_numpy(force),
        time=time,
        steps=step,
        initial_diagnostics=initial_diagnostics,
        final_diagnostics=final_diagnostics,
        absorber_inserted=absorber_inserted,
        frames=tuple(frames),
    )
####


def radiant_wave_config(
    dimensions: int,
    resolution: int,
    final_time: float,
    backend: BackendName = "numpy",
    diffusion_method: DiffusionMethod = "auto",
    material_layout: MaterialLayout = "slab",
) -> RadiantWaveConfig:
    return RadiantWaveConfig(
        dimensions=cast(RadiantDimension, dimensions),
        resolution=(resolution,) * dimensions,
        final_time=final_time,
        backend=backend,
        diffusion_method=diffusion_method,
        material_layout=material_layout,
    )
####
