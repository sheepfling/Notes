from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from converging_flow.backend import BackendName

Dimension = Literal[1, 2, 3]


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Configuration for an inert compressible-flow convergence experiment."""

    dimensions: Dimension
    resolution: tuple[int, ...]
    backend: BackendName = "numpy"
    half_extent: float = 1.0
    gamma: float = 1.4
    cfl: float = 0.35
    final_time: float = 0.18
    max_steps: int = 20_000
    ambient_density: float = 1.0
    ambient_pressure: float = 1.0
    shell_radius: float = 0.58
    shell_width: float = 0.11
    inward_mach: float = 0.75
    density_floor: float = 1.0e-8
    pressure_floor: float = 1.0e-8

    def __post_init__(self) -> None:
        if self.dimensions not in (1, 2, 3):
            raise ValueError("dimensions must be 1, 2, or 3")
        ####
        if len(self.resolution) != self.dimensions:
            raise ValueError("resolution length must match dimensions")
        ####
        if self.backend not in ("auto", "numpy", "cupy"):
            raise ValueError("backend must be 'auto', 'numpy', or 'cupy'")
        ####
        if any(size < 8 for size in self.resolution):
            raise ValueError("each resolution entry must be at least 8")
        ####
        if self.half_extent <= 0.0:
            raise ValueError("half_extent must be positive")
        ####
        if self.gamma <= 1.0:
            raise ValueError("gamma must be greater than 1")
        ####
        if not 0.0 < self.cfl < 1.0:
            raise ValueError("cfl must be between 0 and 1")
        ####
        if self.final_time <= 0.0:
            raise ValueError("final_time must be positive")
        ####
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        ####
        if self.ambient_density <= 0.0 or self.ambient_pressure <= 0.0:
            raise ValueError("ambient density and pressure must be positive")
        ####
        if not 0.0 < self.shell_radius < self.half_extent:
            raise ValueError("shell_radius must lie inside the domain")
        ####
        if self.shell_width <= 0.0:
            raise ValueError("shell_width must be positive")
        ####
        if self.inward_mach < 0.0:
            raise ValueError("inward_mach cannot be negative")
        ####
    ####

    @property
    def spacing(self) -> tuple[float, ...]:
        return tuple(2.0 * self.half_extent / size for size in self.resolution)
    ####
####
