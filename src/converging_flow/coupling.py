"""Solver-independent field coupling operators for staged experiments."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class NormalizedWeightedCoupling:
    """Combine normalized source fields into a bounded target permission field."""

    weights: tuple[tuple[str, float], ...]
    baseline: float = 0.0

    def __post_init__(self) -> None:
        if not self.weights:
            raise ValueError("a coupling requires at least one weighted field")
        ####
        if any(not name or weight < 0.0 for name, weight in self.weights):
            raise ValueError(
                "coupling names must be non-empty with non-negative weights"
            )
        ####
        if self.baseline < 0.0:
            raise ValueError("coupling baseline cannot be negative")
        ####
    ####

    def apply(
        self,
        fields: Mapping[str, FloatArray],
        envelope: FloatArray | None = None,
    ) -> FloatArray:
        """Return a normalized weighted sum, optionally gated by an envelope."""
        first_name = self.weights[0][0]
        try:
            result = np.full_like(fields[first_name], self.baseline, dtype=np.float64)
        except KeyError as error:
            raise ValueError(f"missing coupling field: {first_name}") from error
        ####
        for name, weight in self.weights:
            try:
                values = np.asarray(fields[name], dtype=np.float64)
            except KeyError as error:
                raise ValueError(f"missing coupling field: {name}") from error
            ####
            if values.shape != result.shape:
                raise ValueError("all coupling fields must have the same shape")
            ####
            scale = max(float(np.max(np.abs(values))), 1.0e-12)
            result += weight * values / scale
        ####
        if envelope is not None:
            if envelope.shape != result.shape:
                raise ValueError("coupling envelope must match field shape")
            ####
            result *= envelope
        ####
        maximum = max(float(np.max(result)), 1.0e-12)
        return np.clip(result / maximum, 0.0, 1.0)
    ####
####
