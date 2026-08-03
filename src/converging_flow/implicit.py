from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from converging_flow.backend import Array, ArrayBackend
from converging_flow.stencils import (
    conservative_flux_divergence,
    negative_operator_diagonal,
)

DiffusionMethod = Literal["auto", "explicit", "crank-nicolson"]


@dataclass(frozen=True, slots=True)
class LinearSolverConfig:
    """Controls the matrix-free Krylov solve used by implicit diffusion."""

    relative_tolerance: float = 1.0e-8
    absolute_tolerance: float = 0.0
    restart: int = 24
    maximum_iterations: int = 120

    def __post_init__(self) -> None:
        if self.relative_tolerance <= 0.0:
            raise ValueError("relative_tolerance must be positive")
        ####
        if self.absolute_tolerance < 0.0:
            raise ValueError("absolute_tolerance cannot be negative")
        ####
        if self.restart < 2:
            raise ValueError("restart must be at least two")
        ####
        if self.maximum_iterations < 1:
            raise ValueError("maximum_iterations must be positive")
        ####
    ####
####


def diffusion_rate(
    values: Array,
    coefficient: Array,
    spacing: tuple[float, ...],
    backend: ArrayBackend,
    capacity: Array | None = None,
) -> Array:
    rate = conservative_flux_divergence(
        values,
        coefficient,
        spacing,
        backend,
    )
    if capacity is not None:
        rate = rate / capacity
    ####
    return rate
####


def explicit_midpoint_diffusion(
    values: Array,
    coefficient: Array,
    spacing: tuple[float, ...],
    timestep: float,
    backend: ArrayBackend,
    capacity: Array | None = None,
) -> Array:
    first_rate = diffusion_rate(
        values,
        coefficient,
        spacing,
        backend,
        capacity,
    )
    midpoint = values + 0.5 * timestep * first_rate
    second_rate = diffusion_rate(
        midpoint,
        coefficient,
        spacing,
        backend,
        capacity,
    )
    return values + timestep * second_rate
####


def crank_nicolson_diffusion(
    values: Array,
    coefficient: Array,
    spacing: tuple[float, ...],
    timestep: float,
    backend: ArrayBackend,
    solver: LinearSolverConfig,
    capacity: Array | None = None,
) -> Array:
    """Solve one variable-coefficient Crank-Nicolson diffusion step.

    The operator is matrix-free, so the same implementation dispatches to
    SciPy GMRES on CPU and CuPy GMRES on GPU without assembling a 3D sparse
    matrix.
    """
    if timestep <= 0.0:
        raise ValueError("timestep must be positive")
    ####

    theta_timestep = 0.5 * timestep
    right_hand_side = values + theta_timestep * diffusion_rate(
        values,
        coefficient,
        spacing,
        backend,
        capacity,
    )
    shape = tuple(int(size) for size in values.shape)
    size = int(values.size)

    def matvec(vector: Array) -> Array:
        field = vector.reshape(shape)
        applied = field - theta_timestep * diffusion_rate(
            field,
            coefficient,
            spacing,
            backend,
            capacity,
        )
        return applied.ravel()
    ####

    operator = backend.linear_operator(
        (size, size),
        matvec,
        dtype=np.float64,
    )

    operator_diagonal = 1.0 + theta_timestep * negative_operator_diagonal(
        coefficient,
        spacing,
        backend,
        capacity,
    )

    def precondition(vector: Array) -> Array:
        return (vector.reshape(shape) / operator_diagonal).ravel()
    ####

    preconditioner = backend.linear_operator(
        (size, size),
        precondition,
        dtype=np.float64,
    )
    solution, info = backend.gmres_solver(
        operator,
        right_hand_side.ravel(),
        x0=values.ravel(),
        rtol=solver.relative_tolerance,
        atol=solver.absolute_tolerance,
        restart=solver.restart,
        maxiter=solver.maximum_iterations,
        M=preconditioner,
    )
    information = int(info)
    if information != 0:
        raise RuntimeError(
            "Crank-Nicolson GMRES did not converge; "
            f"backend={backend.name}, info={information}"
        )
    ####
    return solution.reshape(shape)
####


def advance_diffusion(
    values: Array,
    coefficient: Array,
    spacing: tuple[float, ...],
    timestep: float,
    backend: ArrayBackend,
    method: DiffusionMethod,
    solver: LinearSolverConfig,
    capacity: Array | None = None,
) -> Array:
    if method == "explicit":
        return explicit_midpoint_diffusion(
            values,
            coefficient,
            spacing,
            timestep,
            backend,
            capacity,
        )
    ####
    if method == "crank-nicolson":
        return crank_nicolson_diffusion(
            values,
            coefficient,
            spacing,
            timestep,
            backend,
            solver,
            capacity,
        )
    ####
    raise ValueError(f"unsupported diffusion method: {method}")
####
