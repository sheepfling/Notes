"""Generic schedules for changing material fields during a simulation.

The objects in this module describe *what* changes in space and time.  They do
not know which solver consumes the fields, so the same event description can be
used by scalar-wave, Euler, or future transport experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]
MaterialPropertyName = Literal[
    "activity_diffusivity",
    "growth_rate",
    "loss_rate",
    "thermal_conductivity",
    "heat_capacity",
    "heat_loss_rate",
    "wave_density",
    "wave_stiffness",
    "wave_damping",
]


@dataclass(frozen=True, slots=True)
class LinearRamp:
    """A bounded linear fraction that starts at zero and reaches a final value."""

    start_time: float
    end_time: float
    final_fraction: float = 1.0

    def __post_init__(self) -> None:
        if self.start_time < 0.0 or self.end_time < self.start_time:
            raise ValueError("ramp times must be ordered non-negative values")
        ####
        if not 0.0 <= self.final_fraction <= 1.0:
            raise ValueError("final_fraction must lie between zero and one")
        ####
    ####

    def fraction_at(self, time: float) -> float:
        """Return the completed fraction at ``time``."""
        if time < self.start_time:
            return 0.0
        ####
        if self.end_time == self.start_time or time >= self.end_time:
            return self.final_fraction
        ####
        return (
            self.final_fraction
            * (time - self.start_time)
            / (self.end_time - self.start_time)
        )
    ####

    def next_boundary_after(self, time: float) -> float | None:
        """Return the next discontinuous schedule boundary, if one remains."""
        if time < self.start_time:
            return self.start_time
        ####
        if self.end_time == self.start_time and time < self.end_time:
            return self.end_time
        ####
        return None
    ####
####


@dataclass(frozen=True, slots=True)
class MaterialReplacementEvent:
    """Replace an ordered part of a region with one material over a time ramp.

    ``rank`` encodes insertion order within ``region``: cells with lower rank
    are replaced first.  A constant zero rank yields an instantaneous whole
    region replacement; an axial rank yields a progressively inserted rod.
    """

    name: str
    target_material_id: int
    region: BoolArray
    rank: FloatArray
    ramp: LinearRamp

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("material event name cannot be empty")
        ####
        if self.region.shape != self.rank.shape:
            raise ValueError("event region and rank must have the same shape")
        ####
        if not np.any(self.region):
            raise ValueError("material event region cannot be empty")
        ####
        if not np.all(np.isfinite(self.rank)):
            raise ValueError("event rank must be finite")
        ####
        if np.any(self.rank[self.region] < 0.0) or np.any(self.rank[self.region] > 1.0):
            raise ValueError("event rank must lie in [0, 1] within its region")
        ####
    ####

    def mask_at(self, time: float) -> BoolArray:
        """Return the cells replaced at ``time``."""
        return self.region & (self.rank <= self.ramp.fraction_at(time))
    ####

    def progress_at(self, time: float) -> float:
        return self.ramp.fraction_at(time)
    ####
####


@dataclass(frozen=True, slots=True)
class MaterialPropertyRamp:
    """Add a time-ramped property offset within a fixed spatial region."""

    name: str
    property_name: MaterialPropertyName
    region: BoolArray
    amplitude: float
    ramp: LinearRamp

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("property event name cannot be empty")
        ####
        if not np.any(self.region):
            raise ValueError("property event region cannot be empty")
        ####
        if not np.isfinite(self.amplitude) or self.amplitude < 0.0:
            raise ValueError("property event amplitude must be finite and non-negative")
        ####
    ####

    def offset_at(self, time: float) -> float:
        return self.amplitude * self.ramp.fraction_at(time)
    ####
####


@dataclass(frozen=True, slots=True)
class MaterialEventSchedule:
    """A solver-independent collection of timed material-field changes."""

    replacements: tuple[MaterialReplacementEvent, ...] = ()
    property_ramps: tuple[MaterialPropertyRamp, ...] = ()

    def __post_init__(self) -> None:
        names = [event.name for event in self.replacements]
        names.extend(event.name for event in self.property_ramps)
        if len(names) != len(set(names)):
            raise ValueError("material event names must be unique")
        ####
    ####

    def next_boundary_after(self, time: float) -> float | None:
        boundaries = [
            boundary
            for event in (*self.replacements, *self.property_ramps)
            if (boundary := event.ramp.next_boundary_after(time)) is not None
        ]
        return min(boundaries) if boundaries else None
    ####

    def progress_at(self, time: float) -> tuple[float, ...]:
        return tuple(event.progress_at(time) for event in self.replacements)
    ####
####
