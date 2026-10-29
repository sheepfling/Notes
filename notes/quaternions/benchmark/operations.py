#!/usr/bin/env python3
"""Reproducible, allocation-included quaternion microbenchmarks (no installs).

Run: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
     python benchmark.py --output results.json

Inputs: seeded float64 unit quaternions in w,x,y,z order and float64 vectors.
Composition is Hamilton q1*q2 (q2 applied first); active right-handed rotation.
No generated code, JIT, GPU, threading, or dependency installation is used.
"""

import argparse
import contextlib
import datetime
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
import pathlib
import platform
import random
import statistics
import sys
import time
import timeit

import numpy as np
import scipy
import rowan
import pylinalg
from scipy.spatial.transform import Rotation
try:
    import quaternion as qlib
except ImportError:
    qlib = None


def multiply_python(a, b):
    w, x, y, z = a
    W, X, Y, Z = b
    return (w*W-x*X-y*Y-z*Z, w*X+x*W+y*Z-z*Y,
            w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W)


def multiply_numpy(a, b):
    w, x, y, z = np.moveaxis(a, -1, 0)
    W, X, Y, Z = np.moveaxis(b, -1, 0)
    return np.stack((w*W-x*X-y*Y-z*Z, w*X+x*W+y*Z-z*Y,
                     w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W), axis=-1)


def rotate_python(q, v):
    w, x, y, z = q
    vx, vy, vz = v
    tx, ty, tz = 2*(y*vz-z*vy), 2*(z*vx-x*vz), 2*(x*vy-y*vx)
    return (vx+w*tx+y*tz-z*ty, vy+w*ty+z*tx-x*tz, vz+w*tz+x*ty-y*tx)


def rotate_numpy(q, v):
    w, x, y, z = np.moveaxis(q, -1, 0)
    vx, vy, vz = np.moveaxis(v, -1, 0)
    tx, ty, tz = 2*(y*vz-z*vy), 2*(z*vx-x*vz), 2*(x*vy-y*vx)
    return np.stack((vx+w*tx+y*tz-z*ty, vy+w*ty+z*tx-x*tz,
                     vz+w*tz+x*ty-y*tx), axis=-1)


def python_batch(fn, a, b):
    return [fn(x, y) for x, y in zip(a, b)]


def python_array(fn, a, b, scalar):
    if scalar:
        return np.asarray(fn(a.tolist(), b.tolist()))
    return np.asarray(python_batch(fn, a.tolist(), b.tolist()))


def scipy_multiply_array(a, b):
    return (Rotation.from_quat(a, scalar_first=True) *
            Rotation.from_quat(b, scalar_first=True)).as_quat(scalar_first=True)


def scipy_rotate_array(q, v):
    return Rotation.from_quat(q, scalar_first=True).apply(v)


def qlib_multiply_array(a, b):
    return qlib.as_float_array(qlib.as_quat_array(a) * qlib.as_quat_array(b))


def qlib_rotate_prepared(q, pure_v):
    # Paired operands, not rotate_vectors' Cartesian-product batch semantics.
    return qlib.as_vector_part(q * pure_v * q.conjugate())


def qlib_rotate_array(q, v):
    # Match the contiguous (N,3) output contract of the other array paths.
    return np.ascontiguousarray(qlib_rotate_prepared(qlib.as_quat_array(q), qlib.from_vector_part(v)))


def to_xyzw(q):
    return np.ascontiguousarray(q[..., [1, 2, 3, 0]])


def to_wxyz(q):
    return np.ascontiguousarray(q[..., [3, 0, 1, 2]])


def rowan_rotate_array(q, v):
    return np.ascontiguousarray(rowan.rotate(q, v))


def pylinalg_multiply_prepared(a, b):
    # Installed quat_mul is a scalar API: explicitly loop rather than claim
    # vectorization for paired batch inputs. Native order is x,y,z,w.
    if a.ndim == 1:
        return pylinalg.quat_mul(a, b)
    return np.stack([pylinalg.quat_mul(x, y) for x, y in zip(a, b)])


def pylinalg_rotate_prepared(q, v):
    if q.ndim == 1:
        return pylinalg.vec_transform_quat(v, q)
    return np.stack([pylinalg.vec_transform_quat(x, a) for a, x in zip(q, v)])


def pylinalg_multiply_array(a, b):
    return to_wxyz(pylinalg_multiply_prepared(to_xyzw(a), to_xyzw(b)))


def pylinalg_rotate_array(q, v):
    return np.ascontiguousarray(pylinalg_rotate_prepared(to_xyzw(q), v))


def assert_close(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=2e-13, atol=2e-13)


def test_known_cases():
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
    if qlib is not None:
        assert_close(qlib_multiply_array(qi, qj), qk)
        assert_close(qlib_multiply_array(qj, qi), -qk)
    qz90 = np.array([math.sqrt(.5), 0., 0., math.sqrt(.5)])
    vx = np.array([1., 0., 0.])
    vy = np.array([0., 1., 0.])
    functions = [rotate_python, rotate_numpy, scipy_rotate_array, rowan_rotate_array, pylinalg_rotate_array]
    if qlib is not None:
        functions.append(qlib_rotate_array)
    for fn in functions:
        assert_close(fn(qz90, vx), vy)
        assert_close(fn(-qz90, vx), vy)
        assert_close(fn(identity, vx), vx)


def build_cases(seed, sizes):
    rng = np.random.default_rng(seed)
    cases = []
    checks = []
    for n in sizes:
        scalar = n == 1
        shape = (4,) if scalar else (n, 4)
        q1 = rng.normal(size=shape)
        q2 = rng.normal(size=shape)
        q1 /= np.linalg.norm(q1, axis=-1, keepdims=True)
        q2 /= np.linalg.norm(q2, axis=-1, keepdims=True)
        v = rng.normal(size=(3,) if scalar else (n, 3))
        # All conversion/setup here is outside the prepared-operation timer.
        p1, p2, pv = q1.tolist(), q2.tolist(), v.tolist()
        if scalar:
            p1, p2, pv = tuple(p1), tuple(p2), tuple(pv)
        else:
            p1, p2, pv = [tuple(x) for x in p1], [tuple(x) for x in p2], [tuple(x) for x in pv]
        r1 = Rotation.from_quat(q1, scalar_first=True)
        r2 = Rotation.from_quat(q2, scalar_first=True)
        pq1, pq2 = to_xyzw(q1), to_xyzw(q2)
        if qlib is not None:
            nq1, nq2 = qlib.as_quat_array(q1), qlib.as_quat_array(q2)
            nqv = qlib.from_vector_part(v)

        for operation, pyfn, npfn, arrfn, b, pb in (
            ('multiply', multiply_python, multiply_numpy, scipy_multiply_array, q2, p2),
            ('rotate', rotate_python, rotate_numpy, scipy_rotate_array, v, pv),
        ):
            expected = arrfn(q1, b)
            pyval = pyfn(p1, pb) if scalar else python_batch(pyfn, p1, pb)
            npval = npfn(q1, b)
            arrval = python_array(pyfn, q1, b, scalar)
            assert_close(pyval, expected)
            assert_close(npval, expected)
            assert_close(arrval, expected)
            assert np.shape(pyval) == expected.shape
            assert npval.shape == expected.shape
            assert arrval.shape == expected.shape
            assert expected.flags.c_contiguous
            assert npval.flags.c_contiguous
            assert arrval.flags.c_contiguous
            qlib_error = None
            if qlib is not None:
                nqval = qlib_multiply_array(q1, b) if operation == 'multiply' else qlib_rotate_array(q1, b)
                nqnative = qlib.as_float_array(nq1*nq2) if operation == 'multiply' else qlib_rotate_prepared(nq1, nqv)
                assert_close(nqval, expected)
                assert_close(nqnative, expected)
                assert nqval.shape == expected.shape
                assert nqnative.shape == expected.shape
                assert nqval.flags.c_contiguous
                qlib_error = float(np.max(np.abs(nqval-expected)))
            if operation == 'multiply':
                # Independent matrix identity also verifies composition ordering.
                product = Rotation.from_quat(npval, scalar_first=True)
                assert_close(product.as_matrix(), r1.as_matrix() @ r2.as_matrix())
            else:
                assert_close(np.linalg.norm(npval, axis=-1), np.linalg.norm(v, axis=-1))
            checks.append({'n': n, 'operation': operation,
                           'max_abs_python_vs_scipy': float(np.max(np.abs(np.asarray(pyval)-expected))),
                           'max_abs_numpy_vs_scipy': float(np.max(np.abs(npval-expected))),
                           'max_abs_numpy_quaternion_vs_scipy': qlib_error})
            rowfn = rowan.multiply if operation == 'multiply' else rowan_rotate_array
            plfn = pylinalg_multiply_array if operation == 'multiply' else pylinalg_rotate_array
            for name, fn in [('rowan', rowfn), ('pylinalg', plfn)]:
                value = fn(q1, b)
                assert_close(value, expected)
                assert value.shape == expected.shape
                assert value.flags.c_contiguous
                assert value.dtype == np.float64
                checks[-1]['max_abs_' + name + '_vs_scipy'] = float(np.max(np.abs(value-expected)))
            plnative = to_wxyz(pylinalg_multiply_prepared(pq1, pq2)) if operation == 'multiply' else pylinalg_rotate_prepared(pq1, v)
            assert_close(plnative, expected)
            assert plnative.shape == expected.shape
            py_prepared = (lambda fn=pyfn, a=p1, b=pb: fn(a, b)) if scalar else (
                lambda fn=pyfn, a=p1, b=pb: python_batch(fn, a, b))
            np_prepared = lambda fn=npfn, a=q1, b=b: fn(a, b)
            sp_prepared = (lambda a=r1, b=r2: a*b) if operation == 'multiply' else (
                lambda a=r1, b=v: a.apply(b))
            functions = [
                ('prepared', 'python', py_prepared),
                ('prepared', 'numpy', np_prepared),
                ('prepared', 'scipy', sp_prepared),
                ('array_to_array', 'python', lambda fn=pyfn, a=q1, b=b, s=scalar: python_array(fn, a, b, s)),
                ('array_to_array', 'numpy', np_prepared),
                ('array_to_array', 'scipy', lambda fn=arrfn, a=q1, b=b: fn(a, b)),
                ('prepared', 'rowan', (lambda a=q1, b=q2: rowan.multiply(a, b)) if operation == 'multiply' else (lambda a=q1, b=v: rowan.rotate(a, b))),
                ('array_to_array', 'rowan', lambda fn=rowfn, a=q1, b=b: fn(a, b)),
                ('prepared', 'pylinalg', (lambda a=pq1, b=pq2: pylinalg_multiply_prepared(a, b)) if operation == 'multiply' else (lambda a=pq1, b=v: pylinalg_rotate_prepared(a, b))),
                ('array_to_array', 'pylinalg', lambda fn=plfn, a=q1, b=b: fn(a, b)),
            ]
            if qlib is not None:
                nq_prepared = (lambda a=nq1, b=nq2: a*b) if operation == 'multiply' else (
                    lambda a=nq1, b=nqv: qlib_rotate_prepared(a, b))
                nq_arrfn = qlib_multiply_array if operation == 'multiply' else qlib_rotate_array
                functions.extend([
                    ('prepared', 'numpy_quaternion', nq_prepared),
                    ('array_to_array', 'numpy_quaternion', lambda fn=nq_arrfn, a=q1, b=b: fn(a, b)),
                ])
            for path, impl, fn in functions:
                cases.append({'n': n, 'operation': operation, 'path': path,
                              'implementation': impl,
                              'execution': 'explicit_scalar_api_loop' if impl == 'pylinalg' and not scalar else ('python_scalar_loop' if impl == 'python' and not scalar else 'native'),
                              'fn': fn})
    return cases, checks


def environment():
    config = io.StringIO()
    with contextlib.redirect_stdout(config):
        np.show_config()
    cpu = 'unavailable'
    try:
        for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                cpu = line.split(':', 1)[1].strip()
                break
    except OSError:
        pass
    optional = {}
    for module, dist in [('quaternion', 'numpy-quaternion'), ('numba', 'numba'), ('rowan', 'rowan'), ('pylinalg', 'pylinalg')]:
        found = importlib.util.find_spec(module) is not None
        optional[dist] = {'import_available': found}
        try:
            optional[dist]['version'] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            optional[dist]['version'] = None
    return {'python': sys.version, 'python_executable': sys.executable,
            'platform': platform.platform(), 'machine': platform.machine(),
            'reported_cpu': cpu, 'os_cpu_count': os.cpu_count(),
            'numpy': np.__version__, 'scipy': scipy.__version__,
            'numpy_config': config.getvalue(), 'optional_dependencies': optional,
            'thread_environment': {k: os.environ.get(k) for k in (
                'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'SCIPY_ARRAY_API')},
            'timer': vars(time.get_clock_info('perf_counter'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='results.json')
    parser.add_argument('--seed', type=int, default=20261029)
    parser.add_argument('--sizes', type=int, nargs='+', default=[1, 1000, 100000])
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--target-seconds', type=float, default=.05)
    args = parser.parse_args()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print('Checking scalar and paired batch correctness...', flush=True)
    test_known_cases()
    cases, checks = build_cases(args.seed, args.sizes)
    print('Correctness checks passed. Calibrating...', flush=True)
    for case in cases:
        case['fn']()
        case['fn']()
        timer = timeit.Timer(case['fn'])
        number = 1
        while True:
            elapsed = timer.timeit(number=number)
            if elapsed >= args.target_seconds:
                break
            number *= min(10, max(2, math.ceil(args.target_seconds / max(elapsed, 1e-9))))
        case['number'] = number
        case['timer'] = timer
        case['samples_seconds_per_call'] = []
    order_rng = random.Random(args.seed + 1)
    for repeat in range(args.repeats):
        order = list(range(len(cases)))
        order_rng.shuffle(order)
        for index in order:
            case = cases[index]
            elapsed = case['timer'].timeit(number=case['number'])
            case['samples_seconds_per_call'].append(elapsed / case['number'])
        print(f'Repeat {repeat+1}/{args.repeats} completed.', flush=True)
    rows = []
    for case in cases:
        row = {k: v for k, v in case.items() if k not in ('fn', 'timer')}
        samples = row['samples_seconds_per_call']
        row.update({'median_seconds_per_call': statistics.median(samples),
                    'min_seconds_per_call': min(samples), 'max_seconds_per_call': max(samples),
                    'p25_seconds_per_call': float(np.percentile(samples, 25)),
                    'p75_seconds_per_call': float(np.percentile(samples, 75)),
                    'median_nanoseconds_per_element': statistics.median(samples)*1e9/row['n']})
        rows.append(row)
    result = {'started_utc': started,
              'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'script_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              'environment': environment(), 'parameters': vars(args),
              'method': {
                  'inputs': 'Seeded standard-normal float64 arrays; quaternions normalized before all timers; wxyz order; scalar shapes (4,)/(3,), batch shapes (N,4)/(N,3).',
                  'operations': 'Pairwise Hamilton q1*q2; pairwise active right-handed unit quaternion rotation q v q*. No broadcasting one rotation across many vectors.',
                  'prepared': 'Python inputs are Python-float tuples (lists of tuples in batch); NumPy inputs float64 arrays; SciPy Rotation objects preconstructed. numpy-quaternion inputs are quaternion scalars/arrays, with vectors pre-encoded as pure quaternions. Output is native per implementation: Python tuple/list of tuples, NumPy ndarray, SciPy Rotation for multiply and ndarray for rotate; numpy-quaternion quaternion scalar/array for multiply, vector ndarray view for rotate (as_vector_part included).',
                  'array_to_array': 'All inputs and outputs C-contiguous float64 NumPy arrays. Python includes tolist and asarray; SciPy includes from_quat input conversion/normalization and as_quat output extraction for multiplication; numpy-quaternion includes as_quat_array, from_vector_part for rotation and as_float_array/as_vector_part output views, plus ascontiguousarray to copy the strided batch-rotation result into the common contiguous output layout. NumPy is identical to prepared. Compatible numpy-quaternion views need not copy; rotation vector encoding allocates.',
                  'timing': 'timeit.Timer(callable), 2 warmups, loop count calibrated per case to >= target seconds, fixed loop count for repeats, seeded randomized case order each repeat, timer default disables GC during timed loops. Timer callable overhead and allocation/release of outputs included; RNG, initial normalization, correctness tests, imports and prepared representations excluded.',
                  'scope': 'One ephemeral shared/sandboxed host; repeated hot inputs; no affinity control, frequency control, isolation, JIT, memory profiling or threading speedup; no general winner inferred.',
                  'normalization': 'Inputs unit length. Handwritten multiplication does not renormalize output; SciPy Rotation multiplication may enforce normalization. Thus prepared multiplication is a realistic API comparison, not identical primitive arithmetic.',
                  'rowan': 'Native wxyz float arrays. multiply is vectorized; rotate uses a quaternion sandwich and returns a strided batch view. array_to_array includes a contiguous-output copy for rotation.',
                  'pylinalg': 'Native xyzw float arrays. Prepared input ordering conversion excluded; prepared multiply output remains native xyzw. Array-to-array includes wxyz->xyzw input and xyzw->wxyz multiplication-output conversions. Installed scalar-shaped APIs do not provide correct direct paired batches: N>1 measurements use an explicit Python list comprehension of scalar API calls and np.stack. This is an adapter, NOT a native-vectorization result.',
              },
              'correctness': {'passed': True, 'relative_tolerance': 2e-13, 'absolute_tolerance': 2e-13,
                              'known_cases': ['i*j=k', 'j*i=-k', '+90deg z rotates +x to +y', 'q and -q rotate identically', 'identity rotation'],
                              'random_checks': checks, 'additional': ['composition matrix identity for every input', 'rotation preserves vector norms for every input', 'exact scalar or paired batch output shapes for every implementation', 'C-contiguous outputs for all array_to_array implementations']},
              'results': rows}
    pathlib.Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print('n | operation | path | implementation | median us/call | ns/element | range us/call')
    for row in rows:
        print(f"{row['n']:6} | {row['operation']:8} | {row['path']:14} | {row['implementation']:6} | "
              f"{row['median_seconds_per_call']*1e6:12.3f} | {row['median_nanoseconds_per_element']:12.3f} | "
              f"{row['min_seconds_per_call']*1e6:.3f}..{row['max_seconds_per_call']*1e6:.3f}")


if __name__ == '__main__':
    main()
