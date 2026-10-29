#!/usr/bin/env python3
"""Untimed dtype/order/nonunit/native-batch probes for installed versions."""
import hashlib
import importlib.metadata
import inspect
import json
import pathlib
import warnings

import numpy as np
import rowan
import pylinalg
import operations as b


def implementations(op):
    if op == 'multiply':
        return {'python': lambda q, v: b.python_array(b.multiply_python, q, v, q.ndim == 1),
                'numpy': b.multiply_numpy, 'numpy_quaternion': b.qlib_multiply_array,
                'scipy': b.scipy_multiply_array, 'rowan': rowan.multiply,
                'pylinalg': b.pylinalg_multiply_array}
    return {'python': lambda q, v: b.python_array(b.rotate_python, q, v, q.ndim == 1),
            'numpy': b.rotate_numpy, 'numpy_quaternion': b.qlib_rotate_array,
            'scipy': b.scipy_rotate_array, 'rowan': b.rowan_rotate_array,
            'pylinalg': b.pylinalg_rotate_array}


def capture(fn, *args):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            x = np.asarray(fn(*args))
            result = {'status': 'returned', 'value': x.tolist(), 'dtype': str(x.dtype),
                      'shape': list(x.shape), 'c_contiguous': bool(x.flags.c_contiguous)}
        except Exception as e:
            result = {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
        result['warnings'] = [str(w.message) for w in caught]
        return result


def main():
    checks = []
    for dtype in [np.float32, np.float64, np.int64]:
        q = np.array([.5, .5, .5, .5] if dtype != np.int64 else [0, 0, 0, 1], dtype=dtype)
        v = np.array([1, 2, 3], dtype=dtype)
        for op in ['multiply', 'rotate']:
            for name, fn in implementations(op).items():
                result = capture(fn, q, q if op == 'multiply' else v)
                assert result['status'] == 'returned'
                checks.append({'test': 'dtype', 'input_dtype': np.dtype(dtype).name,
                               'operation': op, 'implementation': name, **result})
    # Separate explicit output dtype options: not timed in the float64 benchmark.
    a = np.array([.5, .5, .5, .5], dtype=np.float32)
    v = np.array([1, 2, 3], dtype=np.float32)
    for name, fn in [('multiply', lambda: pylinalg.quat_mul(a, a, dtype=np.float32)),
                     ('rotate', lambda: pylinalg.vec_transform_quat(v, a, dtype=np.float32))]:
        result = capture(fn)
        assert result['dtype'] == 'float32'
        checks.append({'test': 'explicit_pylinalg_output_dtype', 'operation': name, **result})

    qz = np.array([np.sqrt(.5), 0., 0., np.sqrt(.5)])
    vx = np.array([1., 0., 0.])
    for name, fn in implementations('rotate').items():
        for label, q in [('unit', qz), ('scaled_by_2', 2*qz), ('zero', np.zeros(4))]:
            result = capture(fn, q, vx)
            checks.append({'test': 'rotation_norm_policy', 'input': label, 'implementation': name, **result})
            if label == 'unit':
                b.assert_close(result['value'], [0, 1, 0])
            elif label == 'scaled_by_2':
                expected = [-3, 4, 0] if name in ('python', 'numpy') else ([0, 1, 0] if name == 'scipy' else [0, 4, 0])
                b.assert_close(result['value'], expected)
            elif name == 'scipy':
                assert result['status'] == 'error'
            else:
                b.assert_close(result['value'], vx if name in ('python', 'numpy') else [0, 0, 0])
    qi, qj, qk = np.eye(4)[1:]
    for name, fn in implementations('multiply').items():
        result = capture(fn, 2*qi, 3*qj)
        expected = qk if name == 'scipy' else 6*qk
        b.assert_close(result['value'], expected)
        checks.append({'test': 'nonunit_multiply', 'implementation': name, 'expected_policy': 'normalized_rotations' if name == 'scipy' else 'raw_Hamilton_product', **result})
    b.test_known_cases()

    # Probe small shapes only: large unsupported rotation inputs can broadcast
    # an unintended N x N intermediate. Never attempt that at N=100000.
    rng = np.random.default_rng(1)
    probes = []
    for n in [2, 3, 5]:
        q = rng.normal(size=(n, 4)); q /= np.linalg.norm(q, axis=-1, keepdims=True)
        v = rng.normal(size=(n, 3))
        for op, fn, expected in [
            ('multiply', lambda: pylinalg.quat_mul(q, q), (b.Rotation.from_quat(q)*b.Rotation.from_quat(q)).as_quat()),
            ('rotate', lambda: pylinalg.vec_transform_quat(v, q), b.Rotation.from_quat(q).apply(v)),
        ]:
            result = capture(fn)
            result['correct'] = False
            if result['status'] == 'returned':
                value = np.asarray(result['value'])
                result['max_abs_error'] = float(np.max(np.abs(value-expected)))
                result['correct'] = bool(value.shape == expected.shape and np.allclose(value, expected, atol=2e-13, rtol=2e-13))
            assert not result['correct']
            probes.append({'n': n, 'operation': op, 'native_order': 'xyzw', **result})
    # Layout: common contract versus raw/native view for each implementation.
    layouts = []
    q = np.tile(qz, (5, 1)); v = np.tile(vx, (5, 1))
    for op in ['multiply', 'rotate']:
        for name, fn in implementations(op).items():
            result = capture(fn, q, q if op == 'multiply' else v)
            assert result['status'] == 'returned' and result['c_contiguous']
            layouts.append({'path': 'array_to_array', 'operation': op, 'implementation': name, **result})
    for name, fn in [('rowan', lambda: rowan.rotate(q, v)),
                     ('numpy_quaternion', lambda: b.qlib_rotate_prepared(b.qlib.as_quat_array(q), b.qlib.from_vector_part(v)))]:
        result = capture(fn)
        assert not result['c_contiguous']
        layouts.append({'path': 'prepared', 'operation': 'rotate', 'implementation': name, **result})
    source_hashes = {}
    for fn in [rowan.multiply, rowan.rotate, pylinalg.quat_mul, pylinalg.vec_transform_quat]:
        source = inspect.getsource(fn)
        source_hashes[fn.__module__+'.'+fn.__name__] = hashlib.sha256(source.encode()).hexdigest()
    result = {'passed': True, 'versions': {d: importlib.metadata.version(d) for d in ['numpy', 'scipy', 'numpy-quaternion', 'rowan', 'pylinalg']},
              'orders': {'common_contract': 'wxyz', 'python': 'wxyz', 'numpy': 'wxyz', 'numpy_quaternion': 'wxyz', 'rowan': 'wxyz',
                         'scipy': 'xyzw by default; benchmark explicitly scalar_first=True', 'pylinalg': 'xyzw; benchmark converts order'},
              'diagnostics': checks, 'pylinalg_native_batch_probes': probes, 'layouts': layouts,
              'installed_function_source_hashes': source_hashes,
              'scope': 'Untimed observed behavior of these installed functions, not a package-wide conformance suite. Batch probes are small unsupported shape tests; scalar-loop adapters are checked separately by benchmark.py.',
              'script_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              'benchmark_sha256': hashlib.sha256(pathlib.Path(b.__file__).read_bytes()).hexdigest()}
    pathlib.Path('semantics.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Semantic probes passed, including observed non-parity; saved semantics.json.')


if __name__ == '__main__':
    main()
