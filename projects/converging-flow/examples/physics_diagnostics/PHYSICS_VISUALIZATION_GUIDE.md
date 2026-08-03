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

## Impulsive source, pressure wave, and phase transition

### `impulsive_phase_transition/impulsive_phase_space_time.png`

Six aligned space-time views show the finite feedback source, thermodynamic
pressure perturbation, temperature proxy, transformed-phase fraction,
phase-transition drive, and material velocity. The pressure and velocity fields
are Euler quantities, so the outward motion is produced by the conservative
momentum update.

### `impulsive_phase_transition/impulsive_phase_response.png`

This four-panel diagnostic is captured near peak phase-transition drive. It
shows the thermal threshold, current phase fraction alongside its
temperature-equilibrium target, one-way phase drive, and latent-energy storage
density. The gap between current and equilibrium phase makes the finite
transition timescale visible.

### `impulsive_phase_transition/impulsive_pressure_mechanics.png`

This plot directly links thermodynamic pressure to motion at the peak-pressure
frame: pressure perturbation, `-∂p/∂x / ρ` acceleration, and velocity. It is
the actual EOS pressure mechanism, not the scalar-wave pressure proxy.

### `impulsive_phase_transition/impulsive_phase_budget.png`

The budget separates finite source release, internal energy, kinetic energy,
latent phase storage, transformed amount, and the energy residual. Latent
storage rises only after the temperature threshold is reached; it is not a
loss term.

### `impulsive_phase_transition/impulsive_phase_evolution.gif`

The animation uses fixed scales to make the sequence visible: source buildup,
pressure growth, material acceleration, thermal threshold crossing, and phase
conversion. All coefficients are normalized and illustrative.

### `impulsive_phase_transition/impulsive_pressure_wave_evolution.gif`

A second fixed-scale animation isolates the mechanics chain: EOS pressure
perturbation, pressure-gradient acceleration, and resulting material velocity.
Use it when distinguishing the pressure wave from the phase-conversion fields.

## Settled channel block followed by a 2D impulsive event

### `channel_block_impulsive_event/channel_event_handoff.png`

The precursor stage reaches the final channel-block regulation state first.
This figure shows the axial reactive-medium and channel/loss fractions, plus
the axial averages of activity and heat. The last panel is the derived 2D
impulse-permission field passed to the Euler event.

### `channel_block_impulsive_event/channel_event_final_fields.png`

This final 2D panel set shows that the state-derived channel pattern shapes the
finite source progress, thermodynamic pressure perturbation, temperature proxy,
phase fraction, and material speed.

### `channel_block_impulsive_event/channel_event_evolution.gif`

The five-panel animation begins only after the channel-block precursor has
completed. It evolves the 2D Euler event with a fixed, state-derived source map;
the pressure and phase fields are generated by the Euler-plus-phase solver, not
copied from the precursor.

## Perforated block followed by a localized 3D event

### `perforated-block-3d-event/perforated_event_handoff.png`

Shows the event-aligned plane from the settled three-dimensional material map,
scalar activity, heat, scalar wave-pressure proxy, localized event permission,
and Euler initial thermal pressure offset.

### `perforated-block-3d-event/perforated_event_final_fields.png`

Shows the same event-aligned plane after the finite Euler stage: permission,
thermodynamic pressure rise, temperature proxy, source progress, phase
fraction, and material speed.

### `perforated-block-3d-event/perforated_event_stage_history.png`

Separates the pre-event scalar regulation history from the post-event Euler
extrema. The event-enabled marker makes the delayed response sequence explicit.

### `perforated-block-3d-event/perforated_event_evolution.gif`

Fixed-scale frames follow the localized pressure, temperature, activity, phase,
and speed response after the event is enabled. The active plane is selected from
the 3D permission maximum rather than assuming a center slice.

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

PYTHONPATH=src python examples/backend_agnostic/impulsive_phase_transition_demo.py \
  --backend auto \
  --resolution 768 \
  --final-time 0.18 \
  --frames 121 \
  --fps 18 \
  --output examples/physics_diagnostics/impulsive_phase_transition

PYTHONPATH=src python examples/physics_diagnostics/pressure_semantics_comparison.py

PYTHONPATH=src python examples/physics_diagnostics/run_channel_block_impulsive_event.py \
  --backend auto \
  --resolution 48 \
  --final-time 0.16 \
  --frames 101 \
  --fps 16 \
  --output examples/physics_diagnostics/channel_block_impulsive_event
```

The committed `radiant_1d` interface study uses 512 cells, 61 captured frames, a final time
of 1.2, and Crank–Nicolson diffusion. It intentionally omits GIF generation because its
x–t and material-energy plots are the primary diagnostics.
