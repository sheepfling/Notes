from __future__ import annotations

from typing import Any

from converging_flow.backend import Array, ArrayBackend


def harmonic_mean(
    left: Array,
    right: Array,
    backend: ArrayBackend,
) -> Array:
    denominator = left + right
    # ``where=`` and ``out=`` are not accepted by every CuPy ufunc version.
    # Replacing zero denominators keeps the operation portable while the
    # numerator remains zero for the only case where the replacement matters.
    safe_denominator = backend.xp.where(denominator > 0.0, denominator, 1.0)
    return 2.0 * left * right / safe_denominator
####


def conservative_flux_divergence(
    values: Array,
    coefficient: Array,
    spacing: tuple[float, ...],
    backend: ArrayBackend,
) -> Array:
    """Compute div(coefficient grad(values)) with zero-flux outer walls."""
    if values.shape != coefficient.shape:
        raise ValueError("values and coefficient must have identical shapes")
    ####
    if values.ndim != len(spacing):
        raise ValueError("spacing length must match values.ndim")
    ####

    result = backend.xp.zeros_like(values)
    for axis, delta in enumerate(spacing):
        lower_cells: list[Any] = [slice(None)] * values.ndim
        upper_cells: list[Any] = [slice(None)] * values.ndim
        lower_cells[axis] = slice(0, -1)
        upper_cells[axis] = slice(1, None)
        lower = tuple(lower_cells)
        upper = tuple(upper_cells)

        face_coefficient = harmonic_mean(
            coefficient[lower],
            coefficient[upper],
            backend,
        )
        face_flux = face_coefficient * (values[upper] - values[lower]) / delta
        result[lower] += face_flux / delta
        result[upper] -= face_flux / delta
    ####
    return result
####


def negative_operator_diagonal(
    coefficient: Array,
    spacing: tuple[float, ...],
    backend: ArrayBackend,
    capacity: Array | None = None,
) -> Array:
    """Return the positive diagonal of -div(coefficient grad(.))/capacity."""
    diagonal = backend.xp.zeros_like(coefficient)
    for axis, delta in enumerate(spacing):
        lower_cells: list[Any] = [slice(None)] * coefficient.ndim
        upper_cells: list[Any] = [slice(None)] * coefficient.ndim
        lower_cells[axis] = slice(0, -1)
        upper_cells[axis] = slice(1, None)
        lower = tuple(lower_cells)
        upper = tuple(upper_cells)

        face_coefficient = harmonic_mean(
            coefficient[lower],
            coefficient[upper],
            backend,
        ) / (delta * delta)
        diagonal[lower] += face_coefficient
        diagonal[upper] += face_coefficient
    ####
    if capacity is not None:
        diagonal = diagonal / capacity
    ####
    return diagonal
####
