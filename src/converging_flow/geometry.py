"""Reusable Cartesian geometry masks for normalized experiments."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


def spherical_shell_mask(
    coordinates: tuple[FloatArray, FloatArray, FloatArray],
    radius: float,
) -> BoolArray:
    """Return the exterior of a sphere for an arbitrary Cartesian grid."""
    if radius <= 0.0:
        raise ValueError("radius must be positive")
    ####
    x, y, z = np.meshgrid(*coordinates, indexing="ij", sparse=True)
    return np.broadcast_to(x * x + y * y + z * z >= radius * radius, (
        coordinates[0].size,
        coordinates[1].size,
        coordinates[2].size,
    )).copy()
####


def axial_half_mask(
    coordinates: tuple[FloatArray, FloatArray, FloatArray],
    axis: int = 0,
) -> BoolArray:
    """Return the positive half-space along one Cartesian axis."""
    if axis not in (0, 1, 2):
        raise ValueError("axis must be 0, 1, or 2")
    ####
    shape = tuple(values.size for values in coordinates)
    positive = coordinates[axis] > 0.0
    reshape = [1, 1, 1]
    reshape[axis] = positive.size
    return np.broadcast_to(positive.reshape(reshape), shape).copy()
####


def perforated_block_masks(
    coordinates: tuple[FloatArray, FloatArray, FloatArray],
    half_extent: float,
    channel_counts: tuple[int, int] = (6, 4),
    block_fraction: float = 0.82,
    channel_radius_fraction: float = 0.065,
) -> tuple[BoolArray, BoolArray, FloatArray]:
    """Return boundary, axial-passage, and top-to-bottom insertion-rank masks.

    The geometry is intentionally parameterized: a rectangular array of axial
    passages inside a Cartesian block is useful in many generic heat, wave, and
    flow demonstrations.
    """
    if half_extent <= 0.0:
        raise ValueError("half_extent must be positive")
    ####
    if min(channel_counts) < 1:
        raise ValueError("each channel count must be positive")
    ####
    if not 0.0 < block_fraction < 1.0 or channel_radius_fraction <= 0.0:
        raise ValueError("block and channel fractions must be positive")
    ####

    x, y, z = np.meshgrid(*coordinates, indexing="ij", sparse=True)
    block_half_width = block_fraction * half_extent
    active = (
        (np.abs(x) < block_half_width)
        & (np.abs(y) < block_half_width)
        & (np.abs(z) < block_half_width)
    )
    channels = np.zeros(
        (coordinates[0].size, coordinates[1].size, coordinates[2].size), dtype=bool
    )
    radius = channel_radius_fraction * half_extent
    x_centers = np.linspace(-0.55 * half_extent, 0.55 * half_extent, channel_counts[0])
    y_centers = np.linspace(-0.42 * half_extent, 0.42 * half_extent, channel_counts[1])
    for x_center in x_centers:
        for y_center in y_centers:
            channels |= active & (
                (x - x_center) ** 2 + (y - y_center) ** 2 <= radius**2
            )
        ####
    ####

    rank = (block_half_width - z) / (2.0 * block_half_width)
    return ~active, channels, np.broadcast_to(rank, channels.shape).copy()
####
