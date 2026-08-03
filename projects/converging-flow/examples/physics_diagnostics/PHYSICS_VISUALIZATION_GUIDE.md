# Physics Diagnostic Visualization Guide

This gallery is organized around physical questions rather than file types. The radiant-wave
experiment and the reactive-Euler example deliberately use two different pressure concepts:

- **wave-pressure proxy**: normalized scalar-wave energy divided by spatial dimension;
- **thermodynamic pressure**: Euler equation-of-state pressure that enters momentum flux and
  accelerates material.

The former is a diagnostic and feedback field. The latter is a conserved-flow variable.
They should not be combined or interpreted as having the same units.

## Material behavior

### `radiant_3d/material_property_atlas.png`

Nine central-slice maps show every spatially heterogeneous coefficient:

1. autocatalytic growth rate;
2. activity loss rate;
3. activity diffusivity;
4. thermal conductivity;
5. heat capacity;
6. heat loss rate;
7. scalar-wave speed;
8. scalar-wave impedance;
9. scalar-wave damping.

The default materials intentionally keep wave speed similar while changing impedance and
loss. The left material therefore reflects through impedance mismatch; the right material
is approximately impedance-matched but removes energy through damping.

### `radiant_3d/materials.png`

A compact categorical map of reflector, neutral, and absorber regions. Use this beside
field plots to locate interfaces.

## Coupling among state fields

### `radiant_3d/coupling_chain.png`

A synchronized final-time view of:

`activity → heat → wave displacement → wave energy → pressure proxy → force magnitude`

This figure shows correlation and spatial transfer. It does not by itself establish
causality; the budget plots below expose the modeled source and loss terms directly.

### `radiant_3d/coupling_budget_history.png`

Integrated state and rate histories separated into three subsystems:

- activity stock, autocatalytic production, thermal feedback, wave feedback, and loss;
- thermal energy, heat source, and heat loss;
- wave energy, source work, and damping loss.

These rates are normalized model quantities. They are useful for checking sign,
relative importance, saturation, and whether a feedback term actually matters.

## Wave propagation, reflection, and absorption

### `radiant_1d/wave_space_time.png`

An x–t diagram of signed displacement and wave energy. Dashed vertical lines mark material
interfaces. The caption reports normal-incidence amplitude reflection coefficients computed
from impedance:

- neutral to reflector: `R = +0.60`;
- neutral to absorber: `R = +0.00` for the matched default.

The absorber may still contain transmitted energy; absorption is demonstrated by damping
loss, not by requiring the field to vanish immediately at the interface.

### `radiant_1d/material_wave_energy_history.png`

The upper panel tracks wave energy residing in each material. The lower panel integrates
material damping power through time. This separates:

- energy retained or returned by the reflector;
- energy temporarily residing in the neutral slab;
- energy transmitted into and removed by the absorber.

### `radiant_3d/wave_energy_partition.png`

Wave energy is decomposed into:

- kinetic energy: `0.5 * rho_wave * wave_velocity**2`;
- strain energy: `0.5 * stiffness * |grad(wave)|**2`;
- total energy;
- kinetic fraction where total energy is large enough to be meaningful.

Cells below a relative energy threshold are masked in the ratio panel so numerical
roundoff is not displayed as a physical partition.

## Pressure and force direction

### `radiant_3d/pressure_force_direction.png`

The left panel overlays normalized `-grad(wave_pressure)` direction arrows on the wave
pressure proxy. Arrow lengths are normalized; the background and right panel carry the
magnitude information. Low-magnitude arrows are omitted.

This is a **diagnostic force direction**. It does not accelerate the Euler material in the
radiant-wave model.

### `reactive_pressure/reactive_pressure_acceleration.png`

This is the actual pressure-driven-flow chain at an intermediate time:

1. localized heat release raises EOS pressure;
2. `-grad(p) / rho` points away from the high-pressure region;
3. the conservative Euler update develops outward velocity.

No directional pressure body-force term is inserted.

### `pressure_semantics_comparison.png`

A side-by-side comparison of the two pressure concepts:

- left: wave-energy pressure proxy and its derived gradient direction;
- right: Euler thermodynamic pressure perturbation and resulting material velocity.

This is the recommended figure whenever both models are discussed in the same document.

## Reactive-Euler source coupling

### `reactive_pressure/reactive_coupling_chain.png`

Final profiles of progress, pressure, velocity, density, temperature proxy, and total
energy density. It shows how a localized source creates pressure and hydrodynamic response.

### `reactive_pressure/reactive_pressure_space_time.png`

Space–time maps of reaction progress, pressure perturbation, and velocity. This makes the
order of events visible and shows the outward propagation of the response.

### `reactive_pressure/reactive_energy_budget.png`

Four integral diagnostics:

- total energy increase compared with prescribed released heat;
- kinetic energy produced by pressure work;
- energy residual;
- integrated reacted-mass proxy.

The residual remains near floating-point precision in the demonstration.

### `reactive_pressure/reactive_pressure_evolution.gif`

A synchronized animation of progress, thermodynamic pressure, and velocity with fixed axes.

## 3D field animations

The `radiant_3d` directory also contains fixed-scale animations for activity, heat, wave
displacement, and wave pressure. Each animation uses an actual captured solver state rather
than interpolation between only the initial and final fields.

## Reproducing the gallery

```bash
converging-flow radiant-wave-run \
  --dim 3 \
  --n 32 \
  --final-time 0.6 \
  --backend auto \
  --diffusion auto \
  --frames 25 \
  --fps 10 \
  --output examples/physics_diagnostics/radiant_3d

PYTHONPATH=src python examples/backend_agnostic/reactive_pressure_demo.py \
  --backend auto \
  --resolution 512 \
  --final-time 0.08 \
  --frames 25 \
  --fps 10 \
  --output examples/physics_diagnostics/reactive_pressure

PYTHONPATH=src python examples/physics_diagnostics/pressure_semantics_comparison.py
```

The committed `radiant_1d` interface study uses 512 cells, 61 captured frames, a final time
of 1.2, and Crank–Nicolson diffusion. It intentionally omits GIF generation because its
x–t and material-energy plots are the primary diagnostics.
