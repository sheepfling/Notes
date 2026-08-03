from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from typing import Any, Literal, TypeAlias, cast

import numpy as np

BackendName = Literal["auto", "numpy", "cupy"]
ResolvedBackendName = Literal["numpy", "cupy"]
Array: TypeAlias = Any
ArrayModule: TypeAlias = Any
LinearOperatorFactory: TypeAlias = Callable[..., Any]
IterativeSolver: TypeAlias = Callable[..., tuple[Array, int]]


@dataclass(frozen=True, slots=True)
class ArrayBackend:
    """Numerical array and matrix-free linear-algebra backend.

    The explicit ``Any`` boundary is intentional: NumPy and optional CuPy arrays
    do not currently share one practical static ndarray type. The rest of the
    package converts results back to typed NumPy arrays at I/O boundaries.
    """

    name: ResolvedBackendName
    xp: ArrayModule
    linear_operator_factory: LinearOperatorFactory
    gmres_solver: IterativeSolver

    def asarray(self, value: object, *, dtype: object = np.float64) -> Array:
        return self.xp.asarray(value, dtype=dtype)
    ####

    def to_numpy(self, value: Array) -> np.ndarray[Any, np.dtype[np.float64]]:
        if self.name == "numpy":
            return np.asarray(value, dtype=np.float64)
        ####
        cupy = self.xp
        return np.asarray(cupy.asnumpy(value), dtype=np.float64)
    ####

    def scalar(self, value: Array) -> float:
        scalar_value = value.item() if hasattr(value, "item") else value
        return float(scalar_value)
    ####

    def synchronize(self) -> None:
        if self.name == "cupy":
            self.xp.cuda.get_current_stream().synchronize()
        ####
    ####

    def linear_operator(
        self,
        shape: tuple[int, int],
        matvec: Callable[[Array], Array],
        *,
        dtype: object = np.float64,
    ) -> Any:
        return self.linear_operator_factory(
            shape=shape,
            matvec=matvec,
            dtype=dtype,
        )
    ####
####


def _numpy_backend() -> ArrayBackend:
    sparse_linalg = import_module("scipy.sparse.linalg")
    return ArrayBackend(
        name="numpy",
        xp=np,
        linear_operator_factory=cast(
            LinearOperatorFactory,
            sparse_linalg.LinearOperator,
        ),
        gmres_solver=cast(IterativeSolver, sparse_linalg.gmres),
    )
####


def _cupy_backend(*, require_device: bool) -> ArrayBackend:
    try:
        cupy = import_module("cupy")
        sparse_linalg = import_module("cupyx.scipy.sparse.linalg")
    except ImportError as error:
        if find_spec("cupy") is not None:
            raise RuntimeError(
                "CuPy is installed but its CUDA runtime libraries are unavailable; "
                "install the matching CUDA runtime or configure CUDA_PATH"
            ) from error
        ####
        raise RuntimeError(
            "the CuPy backend is not installed; install the optional GPU "
            "dependency with: pip install 'converging-flow[gpu]'"
        ) from error
    ####

    if require_device:
        try:
            device_count = int(cupy.cuda.runtime.getDeviceCount())
        except Exception as error:
            raise RuntimeError("CuPy is installed but no usable CUDA device was found") from error
        ####
        if device_count < 1:
            raise RuntimeError("CuPy is installed but no usable CUDA device was found")
        ####
    ####

    return ArrayBackend(
        name="cupy",
        xp=cupy,
        linear_operator_factory=cast(
            LinearOperatorFactory,
            sparse_linalg.LinearOperator,
        ),
        gmres_solver=cast(IterativeSolver, sparse_linalg.gmres),
    )
####


def get_array_backend(name: BackendName) -> ArrayBackend:
    """Resolve a requested CPU/GPU backend without changing solver physics."""
    if name == "numpy":
        return _numpy_backend()
    ####
    if name == "cupy":
        return _cupy_backend(require_device=True)
    ####
    if name != "auto":
        raise ValueError(f"unsupported backend: {name}")
    ####

    try:
        return _cupy_backend(require_device=True)
    except RuntimeError:
        return _numpy_backend()
    ####
####


def backend_available(name: ResolvedBackendName) -> bool:
    try:
        get_array_backend(name)
    except RuntimeError:
        return False
    ####
    return True
####
