# Backend-neutral PDE and reactive Euler update

## Device boundary

`converging_flow.backend.ArrayBackend` owns the small amount of backend-specific behavior:

- the NumPy or CuPy array namespace;
- conversion into device arrays;
- conversion back to NumPy for artifacts;
- scalar extraction and GPU synchronization;
- matrix-free `LinearOperator` and GMRES construction.

The physics kernels do not branch on CPU versus GPU. The selected array namespace is passed
into conservative stencils, Euler fluxes, diagnostics, and source updates.

## Diffusion integration

RWAS advances local reaction and scalar-wave terms around a full diffusion substep using
Strang splitting:

1. half local/wave midpoint step;
2. full activity and heat diffusion step;
3. half local/wave midpoint step.

The explicit diffusion path uses midpoint RK2. The implicit path solves

```text
(I - dt L / 2) u^(n+1) = (I + dt L / 2) u^n
```

with matrix-free GMRES and a Jacobi preconditioner derived from the conservative face
operator. Heat capacity remains inside the heat operator. Harmonic face coefficients keep
material-interface fluxes consistent.

`--diffusion auto` uses Crank–Nicolson only when the explicit diffusion limit is less than
one quarter of the tightest non-diffusion limit. This avoids paying iterative-solver overhead
on coarse grids where explicit diffusion already takes nearly the same number of steps.

## What “reaction pressure” means

The pressure in compressible flow is not normally an independent directional source. For a
closed reactive gas, the coherent sequence is:

1. advance a transported progress/species variable;
2. convert reacted progress into released internal energy;
3. recover pressure from density, momentum, total energy, and the EOS;
4. let `grad(p)` accelerate the gas through the conservative momentum flux.

The implemented generic state is:

```text
[rho, rho*u_1, ..., rho*u_d, E, rho*lambda]
```

and the source update is:

```text
Delta(rho*lambda) = rho Delta(lambda)
Delta(E) = rho q Delta(lambda)
```

An independently modeled force density may also be supplied. Its impulse changes momentum,
and the exact kinetic-energy change is added to total energy. Passing `-grad(p)` as that
force would double-count pressure.

## Installation

CPU:

```
python -m pip install -e '.[converging-flow]'
```

NVIDIA CUDA 13.x GPU:

```
python -m pip install -e '.[gpu]'
```

Commands:

```
converging-flow run --dim 3 --n 64 --backend auto --no-plots

converging-flow radiant-wave-run \
  --dim 3 \
  --n 64 \
  --backend auto \
  --diffusion auto \
  --no-plots
```

From the repository root, the two article runners keep generated results under
the ignored `artifacts/` tree by default. Explicit `--output` paths remain
available for existing workflows:

```shell
python projects/converging-flow/examples/backend_agnostic/reactive_pressure_demo.py --backend numpy --output artifacts/converging-flow/physics-gallery/reactive_pressure
python projects/converging-flow/examples/backend_agnostic/impulsive_phase_transition_demo.py --backend numpy --output artifacts/converging-flow/impulsive-phase-transition
```

Run the co-located CLI and artifact-routing checks from the repository root:

```shell
python -m pytest projects/converging-flow/examples/backend_agnostic/tests
```

These short checks exercise command routing without running the simulations.
The real gallery orchestration smoke test is documented in the project README;
shared solver tests remain under `tests/converging_flow/`.

## Validation status

The available environment had NumPy/SciPy but no CuPy or CUDA device. CPU execution,
automatic fallback, missing-GPU error handling, explicit/implicit equivalence, and reactive
Euler coupling were executed. The CuPy path uses the matching CuPy array and sparse-linear-
algebra APIs but still requires execution on the target RTX system before claiming measured
GPU parity or speedup.
