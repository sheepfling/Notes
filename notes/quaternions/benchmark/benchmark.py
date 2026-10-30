"""Six-backend list-origin versus prepared-reuse quaternion benchmarks.

All outputs use the same C-contiguous float64 array convention (wxyz or xyz).
No package installation. Requires the versions recorded in the evidence.
"""
import argparse
import hashlib
import json
import math
import pathlib
import pickle
import random
import statistics
import timeit
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Final

import numpy as np
import numpy.typing as npt
import operations as o
import snakemd

_BACKENDS: Final[tuple[str, ...]] = ('python', 'numpy', 'numpy_quaternion', 'scipy', 'rowan', 'pylinalg')


@dataclass(frozen=True)
class ScaleProbe:
    scale: float
    result: list[float]
    passed: bool


@dataclass(frozen=True)
class NormalizerChecks:
    passed: bool
    scale_probes: list[ScaleProbe]
    rejected_invalid_inputs: list[str]


@dataclass(frozen=True)
class CorrectnessCheck:
    n: int
    operation: str
    path: str
    implementation: str
    max_abs_error: float


@dataclass(frozen=True)
class InputSummary:
    n: int
    origin: str
    inputs_unchanged_after_correctness_checks: bool
    raw_q1_norm_range: list[float]
    unit_norm_max_abs_error: float


@dataclass
class TimingCase:
    n: int
    operation: str
    path: str
    implementation: str
    execution: str
    fn: Callable[[], np.ndarray | tuple[np.ndarray, np.ndarray]] = field(repr=False)
    timer: timeit.Timer | None = field(default=None, repr=False)
    number: int = 1
    samples_seconds_per_call: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class CaseSet:
    cases: list[TimingCase]
    correctness: list[CorrectnessCheck]
    inputs: list[InputSummary]


@dataclass(frozen=True)
class TimingResult:
    n: int
    operation: str
    path: str
    implementation: str
    execution: str
    number: int
    samples_seconds_per_call: list[float]
    median_seconds_per_call: float
    min_seconds_per_call: float
    max_seconds_per_call: float
    p25_seconds_per_call: float
    p75_seconds_per_call: float
    median_nanoseconds_per_element: float


@dataclass(frozen=True)
class Tolerance:
    rtol: float
    atol: float


@dataclass(frozen=True)
class RunParameters:
    output: str
    sizes: list[int]
    seed: int
    repeats: int
    target_seconds: float


@dataclass(frozen=True)
class Method:
    origin: str
    outputs: str
    prepared_reuse_common_output: str
    unit_python_lists: str
    raw_python_lists_validated_normalized: str
    preprocessing_only: str
    pylinalg: str
    timing: str
    scope: str


@dataclass(frozen=True)
class CorrectnessReport:
    passed: bool
    tolerance: Tolerance
    checks: list[CorrectnessCheck]


@dataclass(frozen=True)
class BenchmarkReport:
    started_utc: str
    finished_utc: str
    script_sha256: str
    operations_sha256: str
    environment: o.Environment
    parameters: RunParameters
    inputs: list[InputSummary]
    normalizer_checks: NormalizerChecks
    correctness: CorrectnessReport
    method: Method
    results: list[TimingResult]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2) + '\n'



def normalize_quaternion_list(values: npt.ArrayLike) -> np.ndarray:
    """Chosen shared explicit policy: shape/finiteness/nonzero + robust norm.

    This normalization is intentionally the SAME NumPy pipeline for all six
    backends, not a claim to optimize each backend's native normalization API.
    Max-component scaling prevents avoidable norm overflow/underflow.
    """
    q = np.asarray(values, dtype=np.float64)
    if q.ndim not in (1, 2) or q.shape[-1] != 4:
        raise ValueError('quaternions must have shape (4,) or (N,4)')
    if not np.all(np.isfinite(q)):
        raise ValueError('quaternions must be finite')
    scale = np.max(np.abs(q), axis=-1, keepdims=True)
    if np.any(scale == 0):
        raise ValueError('zero quaternion is not a rotation')
    scaled = q / scale
    return np.ascontiguousarray(scaled / np.linalg.norm(scaled, axis=-1, keepdims=True))


def preprocess_raw_lists(operation: str, left: npt.ArrayLike, right: npt.ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    q = normalize_quaternion_list(left)
    if operation == 'multiply':
        rhs = normalize_quaternion_list(right)
        if rhs.shape != q.shape:
            raise ValueError('paired quaternion inputs must have identical shapes')
    else:
        rhs = np.asarray(right, dtype=np.float64)
        if rhs.shape != q.shape[:-1] + (3,):
            raise ValueError('paired vector shape must match quaternion shape')
        if not np.all(np.isfinite(rhs)):
            raise ValueError('vectors must be finite')
        rhs = np.ascontiguousarray(rhs)
    return q, rhs


def run_array(name: str, operation: str, a: npt.ArrayLike, b: npt.ArrayLike) -> np.ndarray:
    """Array-origin operation boundary reused after common preprocessing."""
    if name == 'python':
        fn = o.multiply_python if operation == 'multiply' else o.rotate_python
        return o.python_array(fn, a, b, a.ndim == 1)
    if name == 'numpy':
        return (o.multiply_numpy if operation == 'multiply' else o.rotate_numpy)(a, b)
    if name == 'numpy_quaternion':
        return (o.qlib_multiply_array if operation == 'multiply' else o.qlib_rotate_array)(a, b)
    if name == 'scipy':
        return (o.scipy_multiply_array if operation == 'multiply' else o.scipy_rotate_array)(a, b)
    if name == 'rowan':
        return o.rowan.multiply(a, b) if operation == 'multiply' else o.rowan_rotate_array(a, b)
    if name == 'pylinalg':
        return (o.pylinalg_multiply_array if operation == 'multiply' else o.pylinalg_rotate_array)(a, b)
    raise KeyError(name)


def run_unit_lists(name: str, operation: str, a: npt.ArrayLike, b: npt.ArrayLike, scalar: bool) -> np.ndarray:
    """Actual Python-list input; no explicit norm/validation in this path.

    The data was verified unit outside the timer. Backend coercion is timed.
    SciPy still performs its mandatory constructor normalization.
    """
    if name == 'python':
        fn = o.multiply_python if operation == 'multiply' else o.rotate_python
        return np.asarray(fn(a, b) if scalar else o.python_batch(fn, a, b), dtype=np.float64)
    if name == 'numpy':
        fn = o.multiply_numpy if operation == 'multiply' else o.rotate_numpy
        return fn(np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64))
    if name == 'numpy_quaternion':
        return (o.qlib_multiply_array if operation == 'multiply' else o.qlib_rotate_array)(a, b)
    if name == 'scipy':
        return (o.scipy_multiply_array if operation == 'multiply' else o.scipy_rotate_array)(a, b)
    if name == 'rowan':
        return o.rowan.multiply(a, b) if operation == 'multiply' else o.rowan_rotate_array(a, b)
    if name == 'pylinalg':
        return run_array(name, operation, np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64))
    raise KeyError(name)


def run_normalized_lists(name: str, operation: str, a: npt.ArrayLike, b: npt.ArrayLike) -> np.ndarray:
    q, rhs = preprocess_raw_lists(operation, a, b)
    return run_array(name, operation, q, rhs)


def prepared_callable(name: str, operation: str, q: np.ndarray, rhs: np.ndarray) -> Callable[[], np.ndarray]:
    """Native inputs prepared outside timer, common output conversion inside."""
    scalar = q.ndim == 1
    if name == 'python':
        fn = o.multiply_python if operation == 'multiply' else o.rotate_python
        a, b = q.tolist(), rhs.tolist()
        a, b = (tuple(a), tuple(b)) if scalar else ([tuple(x) for x in a], [tuple(x) for x in b])
        return lambda: np.asarray(fn(a, b) if scalar else o.python_batch(fn, a, b), dtype=np.float64)
    if name == 'numpy':
        return lambda: run_array(name, operation, q, rhs)
    if name == 'rowan':
        return lambda: run_array(name, operation, q, rhs)
    if name == 'numpy_quaternion':
        a = o.qlib.as_quat_array(q)
        if operation == 'multiply':
            b = o.qlib.as_quat_array(rhs)
            return lambda: o.qlib.as_float_array(a*b)
        b = o.qlib.from_vector_part(rhs)
        return lambda: np.ascontiguousarray(o.qlib_rotate_prepared(a, b))
    if name == 'scipy':
        a = o.Rotation.from_quat(q, scalar_first=True)
        if operation == 'multiply':
            b = o.Rotation.from_quat(rhs, scalar_first=True)
            return lambda: (a*b).as_quat(scalar_first=True)
        return lambda: a.apply(rhs)
    if name == 'pylinalg':
        a = o.to_xyzw(q)
        if operation == 'multiply':
            b = o.to_xyzw(rhs)
            return lambda: o.to_wxyz(o.pylinalg_multiply_prepared(a, b))
        return lambda: np.ascontiguousarray(o.pylinalg_rotate_prepared(a, rhs))
    raise KeyError(name)


def check_normalizer() -> NormalizerChecks:
    q = np.array([.5, -.5, .5, -.5])
    probes = []
    for scale in [1e-300, 1e-3, 1., 1e3, 1e300, -1e300]:
        result = normalize_quaternion_list((q*scale).tolist())
        o.assert_close(result, q if scale > 0 else -q)
        o.assert_close(np.linalg.norm(result), 1.)
        probes.append(ScaleProbe(scale, result.tolist(), True))
    bad = [[0., 0., 0., 0.], [1., 0., float('nan'), 0.],
           [float('inf'), 0., 0., 0.], [1., 0., 0.], [[1., 0., 0., 0.], [0., 0., 0., 0.]]]
    rejections = []
    for values in bad:
        try:
            normalize_quaternion_list(values)
        except ValueError as e:
            rejections.append(str(e))
        else:
            raise AssertionError('invalid quaternion was not rejected')
    for op, a, b in [('multiply', [1., 0., 0., 0.], [[1., 0., 0., 0.]]),
                     ('rotate', [1., 0., 0., 0.], [1., 2.]),
                     ('rotate', [1., 0., 0., 0.], [1., float('inf'), 2.])]:
        try:
            preprocess_raw_lists(op, a, b)
        except ValueError as e:
            rejections.append(str(e))
        else:
            raise AssertionError('invalid paired input was not rejected')
    return NormalizerChecks(True, probes, rejections)


def build_cases(seed: int, sizes: Sequence[int]) -> CaseSet:
    rng = np.random.default_rng(seed)
    cases, correctness, inputs = [], [], []
    for n in sizes:
        scalar = n == 1
        shape = (4,) if scalar else (n, 4)
        raw1, raw2 = rng.normal(size=shape), rng.normal(size=shape)
        scaleshape = (1,) if scalar else (n, 1)
        raw1 *= 10**rng.uniform(-3, 3, size=scaleshape)
        raw2 *= 10**rng.uniform(-3, 3, size=scaleshape)
        vectors = rng.normal(size=(3,) if scalar else (n, 3))
        raw1_list, raw2_list, vector_list = raw1.tolist(), raw2.tolist(), vectors.tolist()
        q1, q2 = normalize_quaternion_list(raw1_list), normalize_quaternion_list(raw2_list)
        unit1_list, unit2_list = q1.tolist(), q2.tolist()
        assert isinstance(raw1_list, list) and isinstance(unit1_list, list)
        assert isinstance(raw1_list[0], float) if scalar else isinstance(raw1_list[0], list)
        saved_inputs = [raw1_list, raw2_list, vector_list, unit1_list, unit2_list]
        before_hash = hashlib.sha256(pickle.dumps(saved_inputs)).hexdigest()
        for operation, rhs, raw_rhs, unit_rhs in [('multiply', q2, raw2_list, unit2_list),
                                                 ('rotate', vectors, vector_list, vector_list)]:
            expected = (o.scipy_multiply_array if operation == 'multiply' else o.scipy_rotate_array)(q1, rhs)
            reference_matrix = o.Rotation.from_quat(q1, scalar_first=True)
            if operation == 'multiply':
                product = o.Rotation.from_quat(expected, scalar_first=True)
                other = o.Rotation.from_quat(rhs, scalar_first=True)
                o.assert_close(product.as_matrix(), reference_matrix.as_matrix() @ other.as_matrix())
            else:
                o.assert_close(np.linalg.norm(expected, axis=-1), np.linalg.norm(rhs, axis=-1))
            for name in _BACKENDS:
                functions = [
                    ('prepared_reuse_common_output', prepared_callable(name, operation, q1, rhs)),
                    ('unit_python_lists', lambda name=name, op=operation, a=unit1_list, b=unit_rhs, s=scalar: run_unit_lists(name, op, a, b, s)),
                    ('raw_python_lists_validated_normalized', lambda name=name, op=operation, a=raw1_list, b=raw_rhs: run_normalized_lists(name, op, a, b)),
                ]
                for path, fn in functions:
                    actual = fn()
                    assert actual.shape == expected.shape and actual.dtype == np.float64 and actual.flags.c_contiguous
                    o.assert_close(actual, expected)
                    correctness.append(CorrectnessCheck(n, operation, path, name, float(np.max(np.abs(actual-expected)))))
                    cases.append(TimingCase(n, operation, path, name,
                                  'explicit_scalar_api_loop' if name == 'pylinalg' and not scalar else ('python_scalar_loop' if name == 'python' and not scalar else 'native'), fn))
            # Measured separately: same ingestion/validation/normalization stage,
            # returning its intermediate arrays but performing no operation.
            cases.append(TimingCase(n, operation, 'preprocessing_only', 'shared_numpy_preprocessor', 'native',
                          lambda op=operation, a=raw1_list, b=raw_rhs: preprocess_raw_lists(op, a, b)))
        assert hashlib.sha256(pickle.dumps(saved_inputs)).hexdigest() == before_hash
        inputs.append(InputSummary(n, 'actual Python float list / nested lists', True,
                       [float(np.min(np.linalg.norm(raw1, axis=-1))), float(np.max(np.linalg.norm(raw1, axis=-1)))],
                       float(np.max(np.abs(np.linalg.norm(q1, axis=-1)-1)))))
    return CaseSet(cases, correctness, inputs)


def render_summary(report: BenchmarkReport) -> str:
    """Render the measured medians as Markdown using the SnakeMD package."""
    doc = snakemd.new_doc()
    doc.add_table(
        ['n', 'operation', 'path', 'implementation', 'median us/call'],
        [[str(row.n), row.operation, row.path, row.implementation,
          f'{row.median_seconds_per_call * 1e6:.3f}'] for row in report.results],
    )
    return str(doc)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='results.json')
    parser.add_argument('--sizes', nargs='+', type=int, default=[1, 1000, 100000])
    parser.add_argument('--seed', type=int, default=20261029)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--target-seconds', type=float, default=.05)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    print('Validating actual-list paths, robust normalization, and common outputs...', flush=True)
    normalizer_checks = check_normalizer()
    o.test_known_cases()
    case_set = build_cases(args.seed, args.sizes)
    cases, correctness, inputs = case_set.cases, case_set.correctness, case_set.inputs
    print(f'Correctness passed for {len(correctness)} operation cases; calibrating {len(cases)} timed cases...', flush=True)
    for case in cases:
        case.fn(); case.fn()
        timer, number = timeit.Timer(case.fn), 1
        while True:
            elapsed = timer.timeit(number=number)
            if elapsed >= args.target_seconds:
                break
            number *= min(10, max(2, math.ceil(args.target_seconds/max(elapsed, 1e-9))))
        case.timer, case.number = timer, number
    rng = random.Random(args.seed + 1)
    for repeat in range(args.repeats):
        order = list(range(len(cases))); rng.shuffle(order)
        for i in order:
            case = cases[i]
            assert case.timer is not None
            case.samples_seconds_per_call.append(case.timer.timeit(number=case.number) / case.number)
        print(f'Repeat {repeat+1}/{args.repeats} completed.', flush=True)
    rows: list[TimingResult] = []
    for case in cases:
        samples = case.samples_seconds_per_call
        median = statistics.median(samples)
        rows.append(TimingResult(case.n, case.operation, case.path, case.implementation,
                                 case.execution, case.number, samples, median, min(samples),
                                 max(samples), float(np.percentile(samples, 25)),
                                 float(np.percentile(samples, 75)), median * 1e9 / case.n))
    report = BenchmarkReport(started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
              script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              operations_sha256=hashlib.sha256(pathlib.Path(o.__file__).read_bytes()).hexdigest(),
              environment=o.environment(), parameters=RunParameters(args.output, args.sizes, args.seed, args.repeats, args.target_seconds), inputs=inputs,
              normalizer_checks=normalizer_checks,
              correctness=CorrectnessReport(True, Tolerance(2e-13, 2e-13), correctness),
              method=Method(
                  origin='Unit and raw-list timed callables close over actual Python lists (nested lists for batches). Input-list creation from seeded synthetic data is outside timing; per-call library array/object construction is inside list paths.',
                  outputs='All operation paths return C-contiguous float64 ndarrays, wxyz for multiplication and xyz for rotation, exact scalar or paired batch shape.',
                  prepared_reuse_common_output='Native normalized representations built outside timing; all output extraction/reordering/copying included. This differs from earlier native-output prepared timings.',
                  unit_python_lists='Unit norms verified outside timing, then actual Python lists passed through each backend. No additional explicit norm validation/normalization, but any mandatory backend normalization (e.g. SciPy) remains inside. Python formulas can consume lists directly; other backends construct arrays/objects.',
                  raw_python_lists_validated_normalized='Raw nonunit actual Python lists are first passed through an identical explicit NumPy ingestion/shape/finite/nonzero validation and robust scale-before-norm normalization stage for every backend. Vector lists also converted/validated. Then standard backend construction/operation/output conversion is timed. Python therefore converts normalized ndarrays back to Python floats/lists; SciPy may normalize again. This is a chosen shared-normalizer pipeline, not each backend\'s fastest native normalization strategy.',
                  preprocessing_only='Exact same shared input conversion/validation/normalization stage, timed independently with output allocation/release, but no multiplication/rotation. Do not infer exact stage costs by subtracting separate medians.',
                  pylinalg='Pylinalg 0.6.8 scalar-shaped APIs; batches use explicit scalar-call loops and np.stack. Native input xyzw; conversion cost timed in list paths; outputs wxyz when multiplying. Not native vectorized performance.',
                  timing='timeit.Timer(callable), two warmups, per-case >= target_seconds calibration, fixed loop count per process, five default interleaved shuffled repeats, GC disabled by timeit; all result allocations and dispatch included. Two final independent sequential processes are used.',
                  scope='Shared uncontrolled virtualized host; hot repeated lists/representations; no application ingestion/parser cost, JIT/GPU, allocation-peak measurement, chains, or one-rotation/many-vector benchmark.'),
              results=rows)
    pathlib.Path(args.output).write_text(report.to_json())
    print(render_summary(report))


if __name__ == '__main__':
    main()
