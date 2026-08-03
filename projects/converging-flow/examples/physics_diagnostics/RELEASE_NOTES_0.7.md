# Release 0.7.0 — Physics Diagnostic Visualizations

## Added

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

## Numerical presentation safeguards

- Vector arrows encode direction only; magnitude is shown separately.
- Kinetic-fraction plots mask cells whose total wave energy is negligible.
- Space–time plots use fixed limits and mark material interfaces.
- Energy-loss plots integrate continuous damping power rather than counting per-step decay
  factors.
- The reactive-Euler energy residual is plotted explicitly.

## Compatibility

The solver equations and CPU/GPU backend contract are unchanged. The additional scalar
budget reductions occur only when visualization frames are requested, so production runs
with `--frames 0` do not pay the frame-budget transfer cost.
