"""Construct one unit vector orthogonal to a nonzero vector."""

from __future__ import annotations

import numpy as np


def orthonormal_to(vector: np.ndarray) -> np.ndarray:
    """Return a deterministic unit vector perpendicular to a 1-D input.

    The input must have at least two components and must not be the zero vector.
    Choosing the coordinate axis with the smallest projection avoids unnecessary
    cancellation when the input is normalized.
    """

    value = np.asarray(vector, dtype=float)
    if value.ndim != 1:
        raise ValueError("vector must be one-dimensional")
    ####
    if value.size < 2:
        raise ValueError("vector must have at least two components")
    ####

    squared_norm = float(np.dot(value, value))
    if squared_norm == 0.0:
        raise ValueError("the zero vector has no preferred orthogonal direction")
    ####

    basis = np.zeros_like(value)
    basis[int(np.argmin(np.abs(value)))] = 1.0
    result = basis - (float(np.dot(basis, value)) / squared_norm) * value
    result /= np.linalg.norm(result)
    return result
####

def main() -> None:
    example = np.array([1.0, 2.0, 3.0])
    result = orthonormal_to(example)
    print(result)
    print("dot:", np.dot(example, result))
    print("norm:", np.linalg.norm(result))
####

if __name__ == "__main__":
    main()
####
