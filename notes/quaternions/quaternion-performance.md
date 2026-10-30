# Which Python quaternion implementation won

> Type: reference
> Status: current
> Updated: 2026-10-29

Six implementations, with construction and normalization included.

**In this benchmark, handwritten Python won scalar calls returning NumPy arrays. For 100,000 paired operations, numpy-quaternion had the lowest medians.** But numpy-quaternion's large advantage on prepared inputs shrank sharply when each call started with Python lists.

The useful question is therefore not just “which multiplication is fastest?” It is “what data do I already have, and what must this call return?”

## The winners at three realistic boundaries

All six implementations competed: handwritten Python, a NumPy formula, numpy-quaternion, SciPy `Rotation`, Rowan, and pylinalg. Every path in this new experiment returns **C-contiguous float64 arrays**, with the same shapes and quaternion ordering.

- **Prepared reuse:** native inputs already exist. Time the operation and common-output conversion.
- **Trusted unit lists:** start each call with actual Python lists. Include list-to-array/object construction, the operation, and common output. No extra explicit normalizer is added; SciPy still performs its constructor normalization.
- **Raw lists:** start with nonunit quaternion lists. Add a shared validation/normalization pipeline before backend construction, the operation, and common output.

The table shows the **lowest-median implementation in both runs** for each case. Each range spans two process-run medians, not a confidence interval. Batch times cover all 100,000 pairs.

| Workload | Starting point | Lowest measured implementation | Multiply | Rotate |
|---|---|---|---:|---:|
| Scalar · µs | Prepared reuse | **Python** | 0.695–0.739 | 0.708–0.725 |
| Scalar · µs | Trusted unit lists | **Python** | 0.740–0.813 | 0.748–0.797 |
| Scalar · µs | Raw lists + shared validation/normalization | **Python** | 26.730–30.992 | 16.496–19.144 |
| 100k pairs · ms | Prepared reuse | **numpy-quaternion** | 0.406–0.428 | 1.744–1.759 |
| 100k pairs · ms | Trusted unit lists | **numpy-quaternion** | 49.874–50.515 | 52.022–54.332 |
| 100k pairs · ms | Raw lists + shared validation/normalization | **numpy-quaternion** | 82.062–87.976 | 60.214–60.381 |

**The practical takeaway:** reusing prepared data and rebuilding it from lists are very different workloads. A roughly 0.4 ms prepared batch multiplication does not become a roughly 0.4 ms list-to-result pipeline.

“Lowest measured” is not always a decisive separation. For example, trusted-list 100k rotations took **53.313–59.519 ms** with the NumPy formula, overlapping numpy-quaternion's range. At N=1,000, the NumPy formula had the lowest medians for raw-list rotation. These measurements do not establish a universal winner.

For context, the complete six-way comparison for trusted-unit 100,000-pair calls was:

| Implementation | Multiply · ms | Rotate · ms |
|---|---:|---:|
| Python | 66.735–70.119 | 80.968–91.640 |
| NumPy formula | 55.838–69.081 | 53.313–59.519 |
| numpy-quaternion | 49.874–50.515 | 52.022–54.332 |
| SciPy | 116.607–128.102 | 55.461–61.033 |
| Rowan | 63.943–71.134 | 77.588–86.970 |
| pylinalg, scalar-loop adapter | 2249.799–2309.245 | 3273.620–3376.918 |

## Where the preparation time goes

The shared raw-list preprocessing stage was timed **directly**, without multiplication or rotation:

| Input workload | Units | List ingestion + validation + normalization |
|---|---|---:|
| Scalar multiplication inputs | µs | 25.510–27.080 |
| Scalar rotation inputs | µs | 16.582–17.337 |
| 100k multiplication pairs | ms | 74.497–82.303 |
| 100k rotation pairs | ms | 58.030–65.922 |

This stage converts lists to float64 arrays, checks shapes, finiteness and nonzero quaternion norms, and normalizes using max-component scaling followed by a Euclidean norm. Multiplication normalizes both quaternions; rotation normalizes the quaternion and validates the vector.

Those are combined preprocessing costs, not separate timings for each check or allocation. Backend construction is included in the full list-origin rows above. **Do not subtract independent medians to invent an exact object-construction or normalization cost.** Shared-host noise can even make a standalone-stage median exceed a full-pipeline median.

The normalizer is deliberately the same NumPy pipeline for every backend. Python then converts normalized arrays back to Python numbers; SciPy normalizes again during construction. This measures a specified application policy, not each package's fastest native normalization strategy.

## What the six options actually provide

**numpy-quaternion** is a separate package adding a quaternion dtype to NumPy. The **NumPy formula** is handwritten component arithmetic combining ordinary array operations, not a fused or exhaustively optimized kernel. **Handwritten Python** uses Python-number formulas and loops for batches. [numpy-quaternion documentation](https://quaternion.readthedocs.io/en/stable/), [NumPy ufunc documentation](https://numpy.org/doc/2.3/user/basics.ufuncs.html)

**SciPy Rotation** offers a rotation abstraction and representation conversions. **Rowan** supplies quaternion array operations and passed the paired-batch checks. **Pylinalg's tested functions are scalar-shaped APIs**: its batch results use an explicit Python scalar-loop adapter plus `np.stack`, not native vectorization. Direct paired-array probes failed or, in one case, returned the expected shape with incorrect values. That finding concerns the tested functions in pylinalg 0.6.8, not its entire API. [SciPy](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.spatial.transform.Rotation.html), [Rowan](https://rowan.readthedocs.io/en/latest/package-rowan.html), [pylinalg](https://pylinalg.readthedocs.io/en/latest/reference.html)

## Correctness still comes first

**No implicit normalization** occurs in the chosen raw Rowan, pylinalg, or numpy-quaternion paths; the handwritten rotation shortcut also assumes unit input. SciPy's constructor normalizes. Doubling a unit +90° z quaternion and rotating +x yields `(0,1,0)` through SciPy, `(0,4,0)` through the chosen raw rotation paths, and `(-3,4,0)` through the unit-only shortcut. Trusted-unit timings therefore do not promise equivalent behavior on arbitrary inputs. [SciPy input semantics](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.spatial.transform.Rotation.from_quat.html)

Common quaternion order is `wxyz`; SciPy explicitly uses `scalar_first=True`, and pylinalg's native `xyzw` order is converted. Multiplication applies the second rotation first. All timings are float64; separate probes found different float32 output-dtype behavior. No float32 speed claim follows.

## What to do with this result

- **Single calls on Python numbers:** start with the small Python formula as the baseline, with the required validation policy.
- **Large paired batches:** numpy-quaternion is the measured front-runner here. Include ingestion and output conversion in your own benchmark.
- **Repeated operations on reusable inputs:** construct and validate once when the application genuinely allows it; use the prepared-reuse comparison.
- **Different semantics or features:** choose the appropriate API before comparing speed. This experiment does not cover one rotation applied to many vectors, long chains, interpolation, JIT/GPU kernels, or peak memory.

## Method and limits

Python 3.12.14, NumPy 2.3.5, numpy-quaternion 2024.0.13, SciPy 1.17.0, Rowan 1.3.2, and pylinalg 0.6.8 ran on a virtualized Linux x86_64 shared sandbox reporting an Intel Xeon Platinum 8573C and nine logical CPUs. Thread environment variables `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, and `MKL_NUM_THREADS` were set to 1; affinity, CPU frequency, and competing workloads were not controlled. These are not measurements on the author's personal hardware.

Seed `20261029` generated scalar, 1,000-pair, and 100,000-pair float64 inputs. The raw lists used nonunit random quaternions scaled from 10⁻³ to 10³; the other paths used normalized equivalents. Each case had two warmups, independent loop calibration targeting at least 0.05 seconds, and five shuffled interleaved repeats. Two fresh processes each ran 114 cases, including six preprocessing-only cases. Timing includes output allocation and dispatch; list generation, imports, and correctness checks are outside the timer. `timeit` disables cyclic garbage collection.

Both runs passed checks against normalized SciPy results at relative and absolute tolerance `2e-13`, including Hamilton basis products, identity, +90° rotation, sign equivalence, composition order, vector norms, paired shapes, float64 output, and contiguous layout. The largest observed component discrepancy was `3.109e-15`. The shared normalizer was also tested across scales from 10⁻³⁰⁰ to 10³⁰⁰ and for invalid inputs. These checks do not prove correctness for every input.

The original raw timing samples are retained in a Library bundle outside this repository; access depends on Library permissions, and no public download is provided here. Readers without that access cannot independently audit the original samples or reported medians. The scripts below permit new runs under the documented boundaries; timing varies with the host and workload.

## Reproduce the experiment

The [list-origin harness](benchmark/benchmark.py) and [shared implementations](benchmark/operations.py) reproduce the recorded experiment’s workload. They have since been refactored for typed results and report generation, so they are not byte-for-byte copies of the scripts used for the recorded measurements. The [semantic probes](benchmark/semantics.py) reuse the shared implementations. The harness checks correctness before timing and writes fresh JSON results. Generated results and stdout are local artifacts, not repository inputs.

From the repository root, create a disposable environment with Python 3.12.14 and the recorded numerical package versions. SnakeMD is a later reporting dependency, not part of the original timing environment:

```shell
python3.12 -m venv .venv
.venv/bin/python -m pip install numpy==2.3.5 scipy==1.17.0 \
  numpy-quaternion==2024.0.13 rowan==1.3.2 pylinalg==0.6.8 snakemd==2.4.1
```

Check report serialization and a small smoke run without committing generated evidence:

```shell
.venv/bin/python -m unittest discover -s notes/quaternions/benchmark -p 'test_*.py' -v
```

Run from the artifact directory so generated JSON stays outside tracked files:

```shell
mkdir -p notes/quaternions/benchmark/artifacts
cd notes/quaternions/benchmark/artifacts
../../../../.venv/bin/python ../semantics.py > semantics.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  ../../../../.venv/bin/python ../benchmark.py --output run1.json > run1.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  ../../../../.venv/bin/python ../benchmark.py --output run2.json > run2.txt
```

The full benchmark uses the default three sizes, five repeats, and calibration protocol above; it can take time, particularly for the pylinalg scalar-loop adapter. These are new measurements, not a promise to reproduce the recorded timing on another host. Refactoring and package versions can also change overhead; do not mix new timings with the original results.
