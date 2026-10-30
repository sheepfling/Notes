# Converging Flow release history

These notes preserve the original release reports. Their validation statements describe the
environments in which they were written; they are not results from a new validation run.

## Release 0.7.0 — Physics Diagnostic Visualizations

### Added

- Integrated `RadiantWaveBudget` snapshots with activity, thermal, and wave source/loss
  accounting.
- Per-material wave-energy and damping-loss histories.
- Kinetic and strain wave-energy decomposition.
- Material-property atlas for all nine heterogeneous coefficients.
- Composite coupling-chain visualization.
- Pressure-gradient direction visualization with normalized, thresholded vectors.
- Central-line x–t plots for wave displacement and wave energy.
- Reactive-Euler space–time, pressure-acceleration, coupling-chain, and energy-budget
  visualizations.
- A direct comparison between the scalar-wave pressure proxy and thermodynamic Euler
  pressure.
- Stored frame velocity, wave energy, regional energy, and regional damping data in NPZ
  output.

### Numerical presentation safeguards

- Vector arrows encode direction only; magnitude is shown separately.
- Kinetic-fraction plots mask cells whose total wave energy is negligible.
- Space–time plots use fixed limits and mark material interfaces.
- Energy-loss plots integrate continuous damping power rather than counting per-step decay
  factors.
- The reactive-Euler energy residual is plotted explicitly.

### Compatibility

The solver equations and CPU/GPU backend contract are unchanged. The additional scalar
budget reductions occur only when visualization frames are requested, so production runs
with `--frames 0` do not pay the frame-budget transfer cost.

## Version 0.6.0: backend-neutral arrays, implicit diffusion, and reactive Euler coupling

### Added

- `ArrayBackend` with `auto`, `numpy`, and optional `cupy` selection.
- Backend-neutral conservative Euler flux implementation.
- Matrix-free variable-coefficient Crank–Nicolson diffusion.
- SciPy GMRES on CPU and CuPy GMRES on GPU through one operator contract.
- Jacobi preconditioning derived from harmonic face coefficients.
- Strang splitting between local/wave dynamics and diffusion.
- Automatic explicit-versus-implicit diffusion selection.
- Backend-neutral reactive Euler state with transported reaction progress.
- Energy-release source coupling that raises EOS pressure.
- Optional independently modeled force-density coupling with consistent work.
- A normalized reactive-pressure demonstration and CPU benchmark artifacts.

### Corrected physical interpretation

A reactive gas normally does not receive an arbitrary directional “reaction pressure” body
force. Reaction progress releases internal energy; the equation of state converts that
energy into pressure; the Euler pressure flux accelerates the material. A separate momentum
source belongs only to an independently modeled force or mass/momentum injection process.

### Validation executed here

- 46 pytest tests passed.
- Source and tests compiled successfully.
- NumPy explicit and Crank–Nicolson runs completed.
- Automatic diffusion selection exercised both branches.
- Automatic backend selection fell back to NumPy without CuPy.
- Inert Euler and RWAS installed-wheel CLI smoke tests passed.
- Installed-wheel reactive Euler source smoke test passed.

### Environment limitation

This environment did not contain CuPy or a usable CUDA device. The GPU path is implemented
against CuPy-compatible array and sparse-linear-algebra interfaces, but must be executed on
the target RTX 5080 system before GPU numerical parity or performance is claimed.
