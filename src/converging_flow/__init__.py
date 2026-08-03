"""Vectorized inert-flow and generic reaction-diffusion experiments."""

from converging_flow.backend import ArrayBackend, BackendName, get_array_backend
from converging_flow.config import SimulationConfig
from converging_flow.experiment import (
    RadialProfile,
    SimulationResult,
    VisualizationFrame,
    run_simulation,
)
from converging_flow.radiant_wave import (
    MaterialLayout,
    MaterialProperties,
    RadiantWaveBudget,
    RadiantWaveConfig,
    RadiantWaveFrame,
    RadiantWaveResult,
    run_radiant_wave,
    wave_energy_components,
)
from converging_flow.reaction_diffusion import (
    ReactionDiffusionConfig,
    ReactionFrame,
    ReactionResult,
    run_reaction_diffusion,
)
from converging_flow.reactive_euler import ReactiveEulerConfig

__all__ = [
    "ArrayBackend",
    "BackendName",
    "MaterialLayout",
    "MaterialProperties",
    "RadialProfile",
    "RadiantWaveBudget",
    "RadiantWaveConfig",
    "RadiantWaveFrame",
    "RadiantWaveResult",
    "ReactionDiffusionConfig",
    "ReactionFrame",
    "ReactionResult",
    "ReactiveEulerConfig",
    "SimulationConfig",
    "SimulationResult",
    "VisualizationFrame",
    "get_array_backend",
    "run_radiant_wave",
    "run_reaction_diffusion",
    "run_simulation",
    "wave_energy_components",
]
