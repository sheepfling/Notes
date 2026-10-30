# Reaction backend benchmark

These timings compare one complete second-order midpoint update of the generic activity,
heat, damped-wave, and wave-velocity fields. The Numba timings exclude the one-time JIT
compilation call.

Environment used for this checked example:

- Linux x86-64
- Python 3.13.5
- NumPy 2.3.5
- Numba 0.65.1
- 5 available Numba threads

| Case | Cells | NumPy | Numba | Speedup |
|---|---:|---:|---:|---:|
| 1D, n=4096 | 4,096 | 0.322 ms/step | 0.040 ms/step | 8.11× |
| 2D, n=256 | 65,536 | 4.780 ms/step | 0.745 ms/step | 6.42× |
| 3D, n=64 | 262,144 | 32.441 ms/step | 5.516 ms/step | 5.88× |

The exact ratios depend on CPU, memory bandwidth, thread count, array shape, and run
length. Small one-off simulations may favor NumPy because Numba must compile once per
spatial dimensionality. Repeated runs and larger 2D/3D grids benefit most from the fused
backend.

## Historical command and reproduction status

The original record listed the command below. It is retained for provenance,
but `benchmarks/benchmark_reaction_backends.py` is not present in this
repository, so the command cannot be reproduced from this checkout. The listed
output path is also outside the ignored artifact directory. Do not run it as
written.

```text
PYTHONPATH=src python benchmarks/benchmark_reaction_backends.py \
  --n1 4096 \
  --n2 256 \
  --n3 64 \
  --repetitions 30 \
  --output examples/performance/reaction_backend_benchmark.json
```

If the original harness is recovered, review it and direct any regenerated
reports under the ignored `artifacts/converging-flow/` directory rather than
the source tree. The timings above remain historical observations until the
harness and its environment can be independently verified.
