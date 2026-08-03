# Converging Flow Experiments

This simulation is integrated into the Notes repository. Its maintained package source lives in
`src/converging_flow`, its tests live under `tests/converging_flow`, and generated runs belong in
the ignored `artifacts/converging-flow/` directory.

A coherent, vectorized set of **inert compressible-flow** experiments in 1D, 2D, and 3D.
All three cases use the same conservative Euler equations, ideal-gas EOS, smooth inward
velocity shell, Rusanov finite-volume flux, CFL controller, reflected boundaries,
diagnostics, output schema, and plotting path.

This repository is intentionally **not** a nuclear-weapon model. It contains no explosive
chemistry, detonation-wave model, fissile or fusion reactions, neutron/gamma transport,
weapon geometry, material-property database, or calibration against weapons-test data.
It is suitable for learning, numerical-method development, dimensional consistency tests,
and inert converging-shock studies.

## Why this replaces the earlier scripts

The earlier experiments mixed unrelated partial models without a conserved state or a
consistent discretization. Their most important problems were:

- density was updated as `rho += dt * velocity`, which is dimensionally and physically wrong;
- pressure gradients and spherical geometry were not represented conservatively;
- a density was passed where a volume was expected by the proposed solid EOS;
- integer material IDs were used to index string-keyed dictionaries;
- per-cell loops left scalar values that were later applied to whole arrays;
- light-speed particles were placed inside the hydrodynamic CFL estimate;
- the “advanced” version contained syntax errors and several invalid NumPy expressions;
- global material constants were mutated during timestepping;
- no meaningful verification problem or conservation check existed.

Rather than patch those layers, this project establishes one numerically coherent baseline.

## Experiment mapping

| Experiment | Geometry represented on the Cartesian mesh | Default suite resolution |
|---|---|---:|
| 1D | two-sided planar convergence toward the origin | 512 |
| 2D | circular convergence toward the domain center | 128 × 128 |
| 3D | spherical convergence toward the domain center | 40 × 40 × 40 |

The 1D case is **planar**, not a fake “spherical 1D” coordinate substitution. The shared
initial condition is radial in every available spatial dimension, so the 2D and 3D cases
naturally expose symmetry errors that cannot exist in 1D.

## Install

```bash
uv venv
uv pip install -e '.[dev]'
```

Or with ordinary pip:

```bash
python -m pip install -e '.[dev]'
```

For the optional compiled reaction-diffusion backend without the full developer toolset:

```bash
python -m pip install -e '.[fast]'
```

For NVIDIA CUDA 13.x GPU execution through CuPy:

```bash
python -m pip install -e '.[gpu]'
```

The package keeps CuPy optional. CPU installations do not import it unless the `cupy`
backend is selected, and `auto` falls back to NumPy when no usable CUDA device exists.

## One-command runs

The portable Python runner generates a small smoke suite on Windows, Linux, or macOS:

```bash
python -m converging_flow.runner --backend numpy --reaction-backend numba
```

After installation, the equivalent console command is:

```bash
converging-flow-run --backend auto --output-root artifacts/converging-flow/run
```

From the repository root, the PowerShell helper remains available as a Windows convenience wrapper:

```powershell
.\scripts\run_converging_flow.ps1 -Backend numpy
```

When the virtual environment is not activated, pass its interpreter explicitly:

```powershell
.\scripts\run_converging_flow.ps1 -Python .\.venv-clean\Scripts\python.exe -Backend numpy
```

Use `--backend cupy` (or `-Backend cupy`) to require a CUDA/CuPy device, or `--backend auto` to use the GPU when
available and otherwise fall back to NumPy. The helper keeps CuPy's kernel cache under `.tmp/`.
Add `--full-resolution` (or `-FullResolution`) for the documented default
resolutions. The helper writes Euler, reaction, and radiant-wave outputs under the selected
artifact root.

Run the complete CPU/GPU-aware test suite with:

```powershell
python -m pytest tests/converging_flow -q -rs
```

The CuPy test is skipped with a clear reason when CuPy or a usable CUDA device is unavailable.

## Physics diagnostics gallery

The radiant-wave plots now separate material properties, state fields, transfer budgets,
wave energy, pressure-force diagnostics, and actual Euler pressure-driven motion. The guide
is in [`examples/physics_diagnostics/PHYSICS_VISUALIZATION_GUIDE.md`](examples/physics_diagnostics/PHYSICS_VISUALIZATION_GUIDE.md).

Generate a small backend-agnostic radiant-wave gallery with captured budgets and animations:

```bash
python examples/physics_diagnostics/run_gallery.py \
  --backend auto \
  --final-time 0.04 \
  --frames 9 \
  --output artifacts/converging-flow/physics-gallery
```

Use `--backend numpy` for CPU-only output or `--backend cupy` to require the CUDA GPU.
The runner generates the 1D radiant study, an asymmetric spherical-shell 3D gallery, the reactive-Euler gallery, and
the pressure-semantics comparison in one cross-platform command.

Generate the reactive-Euler pressure/acceleration gallery:

```bash
python examples/backend_agnostic/reactive_pressure_demo.py \
  --backend auto \
  --resolution 128 \
  --final-time 0.04 \
  --frames 9 \
  --output artifacts/converging-flow/physics-diagnostics/reactive_pressure
```

The visualization layer moves only requested frames and integrated scalar budgets to CPU for
plotting; the simulation arrays remain on NumPy or CuPy during integration.

Each captured radiant-wave frame also records a dimensionless `balance_factor`, defined as
normalized source strength divided by normalized sink strength. It is an observational
source-to-loss diagnostic for this toy model—not a nuclear criticality metric, conserved
energy law, or automatic controller. The gallery writes `balance_factor_history.png` and
stores the values in `radiant_wave_state.npz` and `radiant_wave_summary.json`.

To exercise a timed generic absorber insertion and relaxation run:

```bash
python examples/physics_diagnostics/run_absorber_relaxation.py \
  --backend auto \
  --final-time 0.06 \
  --insertion-time 0.03 \
  --frames 61 \
  --output artifacts/converging-flow/absorber-relaxation
```

The `--frames` value should be an integer (for example `9`). The run starts with an open
spherical shell, inserts a generic absorbing right-half region at the chosen time, and saves
`absorber_insertion.png`, `balance_factor_history.png`, the frame-level material masks, and
the balance history for the relaxation phase. The default source and absorber scales are
intentionally exaggerated to make the buildup and reflector-versus-absorber contrast visible;
use `--source-scale` and `--absorber-scale` to tune this generic visualization.

## Run one case

```bash
converging-flow run \
  --dim 2 \
  --n 192 \
  --final-time 0.18 \
  --backend auto \
  --output artifacts/converging-flow/2d
```

## Run the complete suite

```bash
converging-flow suite --output artifacts/converging-flow/suite
```

For a fast smoke run:

```bash
converging-flow suite \
  --n1 256 \
  --n2 64 \
  --n3 24 \
  --final-time 0.12 \
  --output artifacts/converging-flow/smoke
```

Each case writes:

- `state.npz`: conservative and primitive fields plus radial averages;
- `summary.json`: configuration, diagnostics, and conservation drift;
- `density.png`, `pressure.png`, and `speed.png`;
- radial-profile plots for density, pressure, and speed.

The suite also writes cross-dimensional radial-profile comparisons.

## Reaction-diffusion and damped-wave experiments

The package also contains a generic autocatalytic concentration, diffusive heat field,
and damped scalar wave experiment. It is a separate numerical model from the Euler
solver and does not represent nuclear reactions or weapon physics.

Run one case with the portable NumPy backend:

```bash
converging-flow reaction-run \
  --dim 3 \
  --n 48 \
  --final-time 1.0 \
  --backend numpy \
  --output artifacts/converging-flow/reaction-3d
```

For repeated or larger runs, select the optional fused Numba backend:

```bash
converging-flow reaction-run \
  --dim 3 \
  --n 96 \
  --final-time 1.0 \
  --backend numba \
  --output artifacts/converging-flow/reaction-3d-fast
```

The first Numba call compiles one dimensionality-specific kernel. Subsequent steps reuse
that compiled code and four preallocated midpoint arrays.

### Why the old neighbor loops were slow

A Python implementation that loops over every cell and every offset performs up to 27
interpreted inner-loop updates per cell in 3D. Static zones are often recomputed during
every step, decay is applied in an order-dependent way, and temporary history arrays can
dominate memory.

For a toy neighbor-spread rule, the direct vectorized equivalent is a convolution:

```python
from scipy import ndimage

kernel = np.ones((3, 3, 3), dtype=np.float64)
source = activity * np.where(activity > feedback_threshold, feedback_gain, 1.0)
neighbor_sum = ndimage.convolve(source, kernel, mode="constant", cval=0.0)
activity_next = decay * destination_rate * neighbor_sum
```

For heat and waves, a proper finite-difference Laplacian and time integrator are preferable
to repeatedly distributing values to neighbors. The NumPy backend provides the readable
reference implementation. The Numba backend fuses the three Laplacians, local source
terms, clipping, and both midpoint stages into two compiled grid passes.

Run the included benchmark with:

```bash
PYTHONPATH=src python benchmarks/benchmark_reaction_backends.py
```

The committed example timings are machine-specific and exclude one-time Numba compilation.


## Radiant-wave autocatalytic experiment

The `radiant-wave-run` command adds an asymmetric heterogeneous medium without
returning to per-cell neighbor kernels. It advances a bounded autocatalytic activity,
a conservative variable-conductivity heat equation, and a damped scalar wave.

```bash
converging-flow radiant-wave-run \
  --dim 3 \
  --n 48 \
  --final-time 1.0 \
  --backend auto \
  --diffusion auto \
  --frames 20 \
  --output artifacts/converging-flow/radiant-wave-3d
```

Available array backends are `numpy`, `cupy`, and `auto`. State arrays remain on the
selected device throughout the timestep loop. Only saved frames, diagnostics, and final
results are transferred back to NumPy.

Activity and heat diffusion support:

- `explicit`: vectorized explicit midpoint diffusion;
- `crank-nicolson`: matrix-free Crank–Nicolson solved by GMRES;
- `auto`: selects implicit diffusion only when the explicit diffusion limit is much
  tighter than the wave, reaction, and user timestep limits.

The matrix-free form applies the same conservative variable-coefficient face operator on
CPU and GPU and avoids assembling a prohibitively large 3D sparse matrix. Wave propagation
remains explicitly CFL-limited even when diffusion is implicit.

The default first-axis material layout is:

- a high-impedance, weakly damped reflector on the negative side;
- a neutral central slab containing the initial Gaussian activity seed;
- an impedance-matched, strongly damped absorber on the positive side.

Material coefficients enter conservative face fluxes through harmonic means. This
lets interface reflection emerge from impedance contrast instead of manually bouncing
neighbor indices. The absorber uses matched impedance plus continuous damping so that
it removes wave energy without producing a large artificial interface reflection.

The reported `wave_pressure` is a normalized scalar-wave energy-pressure diagnostic.
It is useful for comparing fields and constructing phenomenological feedback, but it is
not an electromagnetic radiation-pressure calculation or a fluid momentum equation.
The derived `force_magnitude` is `|grad(wave_pressure)|` and is likewise diagnostic.

### Timestep-independent decay

The old snippets applied factors such as `0.95` once per step, which changes the physical
decay whenever `dt` changes. The coherent model stores decay as a continuous rate, for
example `-lambda * field`. Over a time interval `dt`, the corresponding exact isolated
decay factor would be `exp(-lambda * dt)`.


## Reactive Euler pressure coupling

A separate backend-neutral `reactive_euler` module demonstrates how a generic reaction
actually produces pressure-driven motion. Its conservative state is:

```text
U = [rho, rho*u_1, ..., rho*u_d, E, rho*lambda]
```

where `lambda` is a bounded reaction-progress fraction. A source substep advances progress
and adds energy:

```text
Delta(rho*lambda) = rho * Delta(lambda)
Delta(E) = rho * q * Delta(lambda)
```

The extra total energy raises pressure through the EOS. The pressure gradient then changes
momentum during the ordinary Euler flux update. A separate momentum source is accepted only
for an independently modeled force density, mass injection, or other real momentum-transfer
mechanism; `-grad(p)` must not be added again as a body force.

Run the included normalized demonstration with:

```bash
PYTHONPATH=src python examples/backend_agnostic/reactive_pressure_demo.py \
  --backend auto \
  --output artifacts/converging-flow/reactive-pressure-demo
```

This demonstration uses a prescribed generic progress-rate profile. It is numerical
infrastructure for combustion-like source coupling, not a calibrated chemistry,
detonation, propulsion, or weapons model.

## Numerical model

The solver advances the inviscid compressible Euler equations:

```text
U = [rho, rho*u_1, ..., rho*u_d, E]
```

with an ideal-gas closure:

```text
p = (gamma - 1) * (E - 0.5 * rho * |u|^2)
```

Interface fluxes use the local Lax-Friedrichs/Rusanov method. It is deliberately first
order: diffusive, but robust and easy to verify before adding reconstruction, limiters, or
more complicated physics. The timestep uses a multidimensional unsplit CFL bound.

The implementation is vectorized over every grid cell. Python loops remain only over the
one to three coordinate axes and over timesteps.

## Validation

Run:

```bash
pytest
```

The current tests verify:

- primitive/conservative conversion round-trips;
- a uniform state remains exactly stationary in 1D, 2D, and 3D;
- short 1D/2D/3D runs remain positive;
- reflected boundaries conserve total mass and energy to floating-point precision;
- radial-profile outputs are finite and correctly shaped.
- reaction, heat, and wave fields remain finite and bounded in 1D, 2D, and 3D;
- NumPy and Numba reaction backends agree to floating-point tolerance;
- reaction output and animation artifacts are generated successfully;
- heterogeneous material fluxes are conservative and constant-preserving;
- reflector and matched-absorber impedance behavior is verified;
- radiant-wave activity, heat, wave energy, pressure, and force fields remain finite;
- automatic CPU/GPU backend resolution and clear missing-CuPy errors;
- Crank–Nicolson constant preservation and agreement with explicit diffusion at small `dt`;
- backend-neutral Euler fluxes agree with the NumPy reference;
- reactive progress is bounded and heat release raises EOS pressure;
- localized energy release creates the expected outward pressure-driven velocity field.

## Deliberate responsibility boundary

This is the baseline to improve before adding more features. The next numerical upgrades
should remain generic and independently testable:

1. MUSCL reconstruction with a slope limiter;
2. HLLC fluxes and a contact-discontinuity test;
3. passive scalar advection for inert material labeling;
4. grid-refinement and rotational-symmetry studies;
5. optional viscosity and thermal diffusion with their own timestep constraints;
6. checkpoint/restart and chunked output for larger 3D runs.

Do not add radiation, phase transitions, or reaction source terms until the underlying
hydrodynamics passes standard verification and convergence tests. Complex source terms do
not repair an incorrect conservation law.
