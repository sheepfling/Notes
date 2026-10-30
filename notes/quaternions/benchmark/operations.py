"""Shared quaternion operations and environment capture for the measured harness.

Inputs use float64 unit quaternions in wxyz order. Hamilton q1*q2 applies
q2 first; rotations are active and right-handed. The list-origin harness owns
measurement and report generation; this module supplies its shared operations.
"""

from __future__ import annotations

import contextlib
import importlib.metadata
import importlib.util
import io
import math
import os
import pathlib
import platform
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
import numpy.typing as npt
import pylinalg
import quaternion as qlib
import rowan
import scipy
from scipy.spatial.transform import Rotation

FloatArray: TypeAlias = npt.NDArray[np.float64]
PythonOperation: TypeAlias = Callable[[Sequence[float], Sequence[float]], tuple[float, ...]]


@dataclass(frozen=True)
class DependencyInfo:
    """Presence and installed distribution version of one dependency."""

    import_available: bool
    version: str | None
####


@dataclass(frozen=True)
class TimerInfo:
    """Clock metadata captured alongside measurements."""

    implementation: str
    monotonic: bool
    adjustable: bool
    resolution: float
####


@dataclass(frozen=True)
class Environment:
    """Execution context recorded in each benchmark report."""

    python: str
    python_executable: str
    platform: str
    machine: str
    reported_cpu: str
    os_cpu_count: int | None
    numpy: str
    scipy: str
    numpy_config: str
    optional_dependencies: dict[str, DependencyInfo]
    thread_environment: dict[str, str | None]
    timer: TimerInfo
####


def multiply_python(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float, float]:
    w, x, y, z = a
    W, X, Y, Z = b
    return (w*W-x*X-y*Y-z*Z, w*X+x*W+y*Z-z*Y,
            w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W)
####


def multiply_numpy(a: FloatArray, b: FloatArray) -> FloatArray:
    w, x, y, z = np.moveaxis(a, -1, 0)
    W, X, Y, Z = np.moveaxis(b, -1, 0)
    return np.stack((w*W-x*X-y*Y-z*Z, w*X+x*W+y*Z-z*Y,
                     w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W), axis=-1)
####


def rotate_python(q: Sequence[float], v: Sequence[float]) -> tuple[float, float, float]:
    w, x, y, z = q
    vx, vy, vz = v
    tx, ty, tz = 2*(y*vz-z*vy), 2*(z*vx-x*vz), 2*(x*vy-y*vx)
    return (vx+w*tx+y*tz-z*ty, vy+w*ty+z*tx-x*tz, vz+w*tz+x*ty-y*tx)
####


def rotate_numpy(q: FloatArray, v: FloatArray) -> FloatArray:
    w, x, y, z = np.moveaxis(q, -1, 0)
    vx, vy, vz = np.moveaxis(v, -1, 0)
    tx, ty, tz = 2*(y*vz-z*vy), 2*(z*vx-x*vz), 2*(x*vy-y*vx)
    return np.stack((vx+w*tx+y*tz-z*ty, vy+w*ty+z*tx-x*tz,
                     vz+w*tz+x*ty-y*tx), axis=-1)
####


def python_batch(fn: PythonOperation, a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> list[tuple[float, ...]]:
    return [fn(x, y) for x, y in zip(a, b)]
####


def python_array(fn: PythonOperation, a: FloatArray, b: FloatArray, scalar: bool) -> FloatArray:
    if scalar:
        return np.asarray(fn(a.tolist(), b.tolist()))
    ####
    return np.asarray(python_batch(fn, a.tolist(), b.tolist()))
####


def scipy_multiply_array(a: npt.ArrayLike, b: npt.ArrayLike) -> FloatArray:
    return (Rotation.from_quat(a, scalar_first=True) *
            Rotation.from_quat(b, scalar_first=True)).as_quat(scalar_first=True)
####


def scipy_rotate_array(q: npt.ArrayLike, v: npt.ArrayLike) -> FloatArray:
    return Rotation.from_quat(q, scalar_first=True).apply(v)
####


def qlib_multiply_array(a: npt.ArrayLike, b: npt.ArrayLike) -> FloatArray:
    return qlib.as_float_array(qlib.as_quat_array(a) * qlib.as_quat_array(b))
####


def qlib_rotate_prepared(
    q: qlib.quaternion | np.ndarray, pure_v: qlib.quaternion | np.ndarray
) -> FloatArray:
    # Paired operands, not rotate_vectors' Cartesian-product batch semantics.
    return qlib.as_vector_part(q * pure_v * q.conjugate())
####


def qlib_rotate_array(q: npt.ArrayLike, v: npt.ArrayLike) -> FloatArray:
    # Match the contiguous (N,3) output contract of the other array paths.
    return np.ascontiguousarray(qlib_rotate_prepared(qlib.as_quat_array(q), qlib.from_vector_part(v)))
####


def to_xyzw(q: FloatArray) -> FloatArray:
    return np.ascontiguousarray(q[..., [1, 2, 3, 0]])
####


def to_wxyz(q: FloatArray) -> FloatArray:
    return np.ascontiguousarray(q[..., [3, 0, 1, 2]])
####


def rowan_rotate_array(q: npt.ArrayLike, v: npt.ArrayLike) -> FloatArray:
    return np.ascontiguousarray(rowan.rotate(q, v))
####


def pylinalg_multiply_prepared(a: FloatArray, b: FloatArray) -> FloatArray:
    # Installed quat_mul is a scalar API: explicitly loop rather than claim
    # vectorization for paired batch inputs. Native order is x,y,z,w.
    if a.ndim == 1:
        return pylinalg.quat_mul(a, b)
    ####
    return np.stack([pylinalg.quat_mul(x, y) for x, y in zip(a, b)])
####


def pylinalg_rotate_prepared(q: FloatArray, v: FloatArray) -> FloatArray:
    if q.ndim == 1:
        return pylinalg.vec_transform_quat(v, q)
    ####
    return np.stack([pylinalg.vec_transform_quat(x, a) for a, x in zip(q, v)])
####


def pylinalg_multiply_array(a: FloatArray, b: FloatArray) -> FloatArray:
    return to_wxyz(pylinalg_multiply_prepared(to_xyzw(a), to_xyzw(b)))
####


def pylinalg_rotate_array(q: FloatArray, v: FloatArray) -> FloatArray:
    return np.ascontiguousarray(pylinalg_rotate_prepared(to_xyzw(q), v))
####


def assert_close(actual: npt.ArrayLike, expected: npt.ArrayLike) -> None:
    np.testing.assert_allclose(np.asarray(actual), np.asarray(expected), rtol=2e-13, atol=2e-13)
####


def test_known_cases() -> None:
    identity = np.array([1., 0., 0., 0.])
    qi, qj, qk = np.eye(4)[1:]
    assert_close(multiply_python(qi.tolist(), qj.tolist()), qk)
    assert_close(multiply_numpy(qi, qj), qk)
    assert_close(scipy_multiply_array(qi, qj), qk)
    assert_close(multiply_python(qj.tolist(), qi.tolist()), -qk)
    assert_close(multiply_numpy(qj, qi), -qk)
    assert_close(scipy_multiply_array(qj, qi), -qk)
    for fn in (rowan.multiply, pylinalg_multiply_array):
        assert_close(fn(qi, qj), qk)
        assert_close(fn(qj, qi), -qk)
    ####
    if qlib is not None:
        assert_close(qlib_multiply_array(qi, qj), qk)
        assert_close(qlib_multiply_array(qj, qi), -qk)
    ####
    qz90 = np.array([math.sqrt(.5), 0., 0., math.sqrt(.5)])
    vx = np.array([1., 0., 0.])
    vy = np.array([0., 1., 0.])
    functions = [rotate_python, rotate_numpy, scipy_rotate_array, rowan_rotate_array, pylinalg_rotate_array]
    if qlib is not None:
        functions.append(qlib_rotate_array)
    ####
    for fn in functions:
        assert_close(fn(qz90, vx), vy)
        assert_close(fn(-qz90, vx), vy)
        assert_close(fn(identity, vx), vx)
    ####
####



def environment() -> Environment:
    """Capture the host, dependencies, configuration and timing clock."""
    config = io.StringIO()
    with contextlib.redirect_stdout(config):
        np.show_config()
    ####
    cpu = 'unavailable'
    try:
        for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                cpu = line.split(':', 1)[1].strip()
                break
            ####
        ####
    except OSError:
        pass
    ####
    optional: dict[str, DependencyInfo] = {}
    for module, dist in (('quaternion', 'numpy-quaternion'), ('numba', 'numba'),
                         ('rowan', 'rowan'), ('pylinalg', 'pylinalg')):
        found = importlib.util.find_spec(module) is not None
        try:
            version = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            version = None
        ####
        optional[dist] = DependencyInfo(import_available=found, version=version)
    ####
    clock = time.get_clock_info('perf_counter')
    return Environment(
        python=sys.version,
        python_executable=sys.executable,
        platform=platform.platform(),
        machine=platform.machine(),
        reported_cpu=cpu,
        os_cpu_count=os.cpu_count(),
        numpy=np.__version__,
        scipy=scipy.__version__,
        numpy_config=config.getvalue(),
        optional_dependencies=optional,
        thread_environment={key: os.environ.get(key) for key in (
            'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'SCIPY_ARRAY_API')},
        timer=TimerInfo(implementation=clock.implementation, monotonic=clock.monotonic,
                        adjustable=clock.adjustable, resolution=clock.resolution),
    )
####
