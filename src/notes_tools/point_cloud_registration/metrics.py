"""Small, dependency-light metrics for comparing point clouds."""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import cKDTree

FloatArray: Final = NDArray[np.float64]


def _points(value: NDArray, name: str) -> FloatArray:
    points = np.asarray(value, dtype=np.float64)
    if points.ndim != 2 or points.shape[0] == 0:
        raise ValueError(f"{name} must be a non-empty [point, dimension] array")
    ####
    if not np.isfinite(points).all():
        raise ValueError(f"{name} contains non-finite values")
    ####
    return points
####


def rmse_nearest(
    reference: NDArray,
    candidate: NDArray,
    *,
    symmetric: bool = True,
) -> float:
    """Measure nearest-neighbor RMSE, optionally averaging both directional means."""

    reference_points = _points(reference, "reference")
    candidate_points = _points(candidate, "candidate")
    reference_tree = cKDTree(reference_points)
    candidate_tree = cKDTree(candidate_points)
    candidate_to_reference, _ = reference_tree.query(candidate_points)
    if not symmetric:
        return float(np.sqrt(np.mean(candidate_to_reference**2)))
    ####

    reference_to_candidate, _ = candidate_tree.query(reference_points)
    return float(
        np.sqrt(
            (np.mean(candidate_to_reference**2) + np.mean(reference_to_candidate**2)) / 2.0
        )
    )
####


def chamfer_distance(reference: NDArray, candidate: NDArray) -> float:
    """Return the sum of mean squared nearest-neighbor distances."""

    reference_points = _points(reference, "reference")
    candidate_points = _points(candidate, "candidate")
    reference_tree = cKDTree(reference_points)
    candidate_tree = cKDTree(candidate_points)
    candidate_to_reference, _ = reference_tree.query(candidate_points)
    reference_to_candidate, _ = candidate_tree.query(reference_points)
    return float(
        np.mean(candidate_to_reference**2) + np.mean(reference_to_candidate**2)
    )
####


def rmse(reference: NDArray, candidate: NDArray) -> float:
    """Return elementwise RMSE for two point arrays with identical shape."""

    reference_points = _points(reference, "reference")
    candidate_points = _points(candidate, "candidate")
    if reference_points.shape != candidate_points.shape:
        raise ValueError("reference and candidate shapes must match")
    ####
    squared_distances = np.sum((reference_points - candidate_points) ** 2, axis=1)
    return float(np.sqrt(np.mean(squared_distances)))
####


def rotation_angle_degrees(
    true_rotation: NDArray | None,
    estimated_rotation: NDArray | None,
) -> float | None:
    """Return the relative 3-D rotation angle, or ``None`` if unavailable."""

    if true_rotation is None or estimated_rotation is None:
        return None
    ####
    true_value = np.asarray(true_rotation, dtype=np.float64)
    estimated_value = np.asarray(estimated_rotation, dtype=np.float64)
    if true_value.shape != (3, 3) or estimated_value.shape != (3, 3):
        raise ValueError("rotation matrices must both have shape [3, 3]")
    ####
    relative = estimated_value @ true_value.T
    cosine = np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))
####


def random_special_orthogonal_matrix(
    dimension: int,
    *,
    rng: np.random.Generator | None = None,
) -> FloatArray:
    """Generate a random proper orthogonal matrix using QR decomposition."""

    if dimension < 1:
        raise ValueError("dimension must be positive")
    ####
    generator = np.random.default_rng() if rng is None else rng
    matrix = generator.normal(size=(dimension, dimension))
    q_matrix, r_matrix = np.linalg.qr(matrix)
    signs = np.sign(np.diag(r_matrix))
    signs[signs == 0.0] = 1.0
    q_matrix *= signs
    if np.linalg.det(q_matrix) < 0.0:
        q_matrix[:, 0] *= -1.0
    ####
    return q_matrix
####
