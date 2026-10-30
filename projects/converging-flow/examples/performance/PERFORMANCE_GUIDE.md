# Efficient grid evolution for reaction, heat, and wave fields

## 1. Separate local physics from spatial operators

Use three distinct operations:

1. **Local source terms** are pointwise NumPy algebra.
2. **Diffusion** uses a Laplacian.
3. **Wave propagation** uses a displacement field plus a velocity field.

Do not represent all three by repeatedly copying a cell value into 26 neighbors. That
operation has no stable timestep interpretation and makes decay depend on loop ordering.

## 2. Exact vectorization of the old toy spread rule

The original destination update can be written as a convolution. If the source feedback is
based on the source cell and the zone multiplier is based on the destination cell:

```python
import numpy as np
from scipy import ndimage

kernel = np.ones((3, 3, 3), dtype=np.float64)
source_gain = np.where(activity > threshold, feedback_gain, 1.0)
source = activity * source_gain
neighbor_sum = ndimage.convolve(
    source,
    kernel,
    mode="constant",
    cval=0.0,
)
activity_next = decay * destination_rate * neighbor_sum
```

This preserves the old 27-neighbor arithmetic without Python cell loops. It is still a toy
spread model, not a heat or wave equation.

## 3. Use a Laplacian for diffusion

For a scalar field `u`, a Cartesian second-order Laplacian is the sum of centered second
differences along each spatial axis. The portable backend pads the field with edge values,
which implements zero-normal-gradient walls without periodic wraparound.

The timestep for explicit diffusion scales with `dx**2`. Doubling the resolution in each
3D direction creates eight times as many cells and approximately four times as many
explicit diffusion steps, or roughly 32 times the total work. At high resolutions, an
implicit or semi-implicit diffusion solve matters more than micro-optimizing one explicit
step.

## 4. Use a signed second-order wave state

Interference requires signed amplitudes. Evolve both wave displacement and wave velocity:

```text
wave_t = wave_velocity
wave_velocity_t = c^2 laplacian(wave) + source - damping * wave_velocity
```

Constructive and destructive interference then occur naturally by addition. A threshold on
two nonnegative arrays is not resonance. Resonance requires time-dependent forcing near a
mode frequency and should be diagnosed from amplitude or energy growth.

## 5. Precompute everything static

Compute these once per run:

- coordinate and radius arrays;
- catalyst and quencher masks;
- local growth and loss fields;
- inverse squared grid spacing;
- stable base timestep;
- output frame times.

The optimized backend does not rebuild these fields during each right-hand-side evaluation.

## 6. Reuse storage

A midpoint method needs temporary states, but those arrays can be allocated once. The fused
backend reuses four midpoint arrays. It does not allocate separate Laplacian, rate,
midpoint, and final arrays for every field during every step.

Store only requested visualization frames. A `96^3` float64 field occupies about 6.75 MiB;
four fields occupy about 27 MiB per full snapshot before metadata or plotting copies.

## 7. Choose a backend by workload

- **NumPy:** best reference implementation, simplest debugging, no compilation pause.
- **Numba:** best for repeated CPU runs and larger 2D/3D grids; fuses loops and temporaries.
- **CuPy/JAX:** useful when grids are large enough to amortize transfer and launch overhead.
- **Implicit SciPy solvers:** useful when diffusion stiffness, rather than per-step cost,
  controls runtime.

Always keep the NumPy backend as the numerical oracle and compare accelerated outputs in
tests.

## 8. Profile the full step

A standalone Laplacian benchmark can be misleading. The important unit is a complete time
step including all fields, source terms, clipping, boundary handling, and integration
stages. The [historical benchmark record](BENCHMARKS.md) describes a measurement
of that complete operation excluding one-time Numba compilation. Its harness is
not present in this repository, so the recorded command cannot currently be
reproduced from this checkout.
