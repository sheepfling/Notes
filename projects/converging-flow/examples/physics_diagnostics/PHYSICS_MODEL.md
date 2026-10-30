# Normalized scalar-field model

This document defines the terminology and equations used by the heterogeneous
reaction–diffusion–wave visualizations. Every coefficient is dimensionless and
illustrative. The model is intended to explain numerical behavior, not to represent a
particular substance or physical system.

## State variables

The simulation advances four fields on a Cartesian grid:

| Symbol | Code field | Interpretation |
| --- | --- | --- |
| `a` | `activity` | bounded scalar concentration or activation level, `0 ≤ a ≤ 1` |
| `T` | `heat` | non-negative normalized thermal state |
| `u` | `wave` | scalar displacement-like field |
| `v = ∂u/∂t` | `wave_velocity` | scalar-wave rate of change |

The wave field is scalar and phenomenological. Its derived pressure-like quantity is a
diagnostic made from wave energy; it is not a mechanical pressure field.

## Material coefficients

Each cell selects a coefficient set from its material label.

| Code property | Symbol | Meaning |
| --- | --- | --- |
| `activity_diffusivity` | `D_a` | spreading coefficient for the activity field |
| `growth_rate` | `g` | local autocatalytic gain |
| `loss_rate` | `λ` | first-order activity decay coefficient |
| `thermal_conductivity` | `κ` | coefficient in the conservative heat flux |
| `heat_capacity` | `C` | thermal storage coefficient |
| `heat_loss_rate` | `h` | first-order thermal loss coefficient |
| `wave_density` | `ρ_w` | inertial coefficient of the scalar wave |
| `wave_stiffness` | `K` | restoring or gradient-energy coefficient |
| `wave_damping` | `γ` | velocity-proportional wave damping |

The terms “reflector”, “reactive medium”, “loss insert”, and “open channel” describe
coefficient regimes only:

- a reflector has relatively high wave impedance and low damping;
- the reactive medium carries the activity and heat source terms;
- a loss insert has high first-order loss and damping;
- an open channel has low activity gain and weak coupling before insertion.

## Continuous equations

With `d` spatial dimensions, the local source terms are:

```text
∂a/∂t = ∇·(D_a ∇a)
        + g a (1 - a) - λ a
        + β T (1 - a) + χ p_w (1 - a)

C ∂T/∂t = ∇·(κ ∇T) + q a - h T

∂u/∂t = v

ρ_w ∂v/∂t = ∇·(K ∇u) + s a - ρ_w γ v
```

Here `β` is thermal feedback, `χ` is wave-pressure feedback, `q` is normalized heat
generation, and `s` is normalized wave driving. The factors `(1 - a)` provide bounded
saturation. The implementation clips the numerical activity and heat fields after each
step to preserve those declared state bounds.

For the channel-block case, the optional distributed exchange parameter `η` modifies the
thermal loss coefficient in the reactive medium according to:

```text
h_eff = h + η f_r
```

where `f_r` is the current loss-insert depth fraction. This is an explicit, normalized
thermal-coupling convenience for the visualization; it is not an inferred material law.

## Wave-derived quantities

The scalar-wave energy density is the sum of kinetic and strain-like terms:

```text
E_w = 1/2 ρ_w v² + 1/2 K |∇u|²
```

The plotted pressure-like diagnostic and force-like magnitude are then:

```text
p_w = E_w / d
F_w = |∇p_w|
```

These definitions make wave energy, gradients, and damping easy to compare across
materials. They do not turn the scalar field into a fluid pressure or a momentum equation.

For a normally incident scalar wave, the coefficient-level wave speed and impedance are:

```text
c_w = √(K / ρ_w)
Z_w = √(ρ_w K)
```

The amplitude reflection estimate at an interface between regimes 1 and 2 is derived from
impedance matching:

```text
R = (Z₂ - Z₁) / (Z₂ + Z₁)
```

The visualizer reports this coefficient as an interface diagnostic. Continuous damping,
rather than a manually reflected wave, removes energy inside a loss insert.

## Source, sink, and balance diagnostics

The reported source and sink strengths are integrated normalized rates:

```text
S = ∫ [g a (1-a) + β T (1-a) + χ p_w (1-a)
       + q a + max(s a v, 0)] dV

L = ∫ [λ a + h T + ρ_w γ v²] dV

k = S / max(L, ε)
```

`k` is an instantaneous source-to-loss ratio. In this generic vocabulary:

- `k > 1` means the current rates are source-dominant;
- `k ≈ 1` means the current rates are near rate balance;
- `k < 1` means the current rates are loss-dominant.

The cumulative source-minus-sink curve is integrated separately with the trapezoidal rule.
It is useful for identifying whether the budget trend reverses, but it is not a conserved
total energy because the model contains prescribed source, feedback, and loss terms.

## Impulsive source and phase-transition Euler model

The `impulsive_phase_transition_demo.py` example is a separate one-dimensional
Euler experiment. It does not use the scalar-wave pressure proxy. Its conserved
state is:

```text
U = [ρ, ρu, E, ρα, ρφ]
```

where `α` is a finite source-progress fraction and `φ` is an irreversible
transformed-phase fraction. Both are bounded between zero and one and advect
with the material. The thermodynamic pressure uses the same calorically perfect
closure as the other Euler example:

```text
p = (γ - 1) [E - 1/2 ρu²]
T_proxy = p / ρ
```

In one spatial dimension, the conservative transport and local source system is:

```text
∂ρ/∂t       + ∂(ρu)/∂x                    = 0
∂(ρu)/∂t    + ∂(ρu² + p)/∂x               = 0
∂E/∂t       + ∂[(E + p)u]/∂x              = ρ q Rα - ρ L Rφ
∂(ρα)/∂t    + ∂(ραu)/∂x                   = ρ Rα
∂(ρφ)/∂t    + ∂(ρφu)/∂x                   = ρ Rφ
```

The actual pressure-gradient acceleration inferred from these equations is

```text
a_pressure = -∂p/∂x / ρ.
```

This is the acceleration shown in the pressure-mechanics plot and animation.
It is distinct from the scalar-wave pressure proxy used by the separate
reaction–diffusion–wave visualization.

The source grows from a nonzero spatial seed but is limited by its remaining
local reservoir:

```text
∂α/∂t = r s(x) α (1 - α)
∂E/∂t = ρ q ∂α/∂t
```

Here `s(x)` is the localized source shape, `r` is the normalized growth rate,
and `q` is released energy per unit mass and progress. This makes the early
event source-dominant and rapid while keeping its total release finite.

The phase transition is driven by a smooth equilibrium fraction evaluated from
the temperature proxy:

```text
φ_eq(T) = 1 / [1 + exp(-(T_proxy - T_transition) / ΔT)]
Rφ = max(φ_eq - φ, 0) / τ_phase
∂φ/∂t = Rφ
∂E/∂t = -ρ L Rφ
```

`L` is normalized latent energy. The last equation transfers energy from the
Euler internal-energy reservoir to phase storage. Consequently the pressure
wave is produced by the EOS after finite source release, while the transition
can temporarily limit the temperature rise. This is a generic normalized
two-state model; it is not a material database, a water/steam calculation, or
a full multiphase equation of state.

The diagnostic outputs therefore have these precise meanings:

| Output | Definition | Interpretation |
| --- | --- | --- |
| pressure perturbation | `Δp = p - p_initial` | EOS pressure wave above the initial ambient state |
| temperature proxy | `T_proxy = p / ρ` | normalized ideal-gas thermal indicator, not calibrated temperature |
| phase target | `φ_eq(T)` | local temperature-equilibrium transformed fraction |
| phase drive | `Rφ` | one-way thermodynamic conversion drive; the source step also caps it by available internal energy |
| latent density | `ρ L φ` | energy stored by the transformed fraction |
| pressure acceleration | `-∂p/∂x / ρ` | local momentum acceleration from the EOS pressure gradient |

The Euler transport step evolves density and momentum, so compression,
expansion, and pressure-wave motion are explicit. No manual pressure
propagation or grid-value stretching is used. Elastic stress, fracture, and
fragmentation are intentionally outside this model and require separately
verified constitutive laws.

The solver uses a source/transport/source split: local finite-source and
latent-energy updates bracket a conservative first-order Rusanov Euler flux
step. The timestep follows the Euler CFL limit. The simple flux is deliberately
dissipative but robust for this qualitative, normalized demonstration; it is
not a shock-resolution or material-calibration claim.

### Scenario validation

Each demonstration run validates its captured history before writing a success
summary. The validation requires finite, bounded source and phase fractions;
a finite source release; a positive pressure perturbation; both negative and
positive material velocity; a transformed-phase fraction above 0.5; and the
ordered milestones

```text
source activation ≤ pressure-wave threshold ≤ phase-transition onset.
```

It also verifies the integrated normalized energy relation

```text
internal energy + kinetic energy + latent storage
  − initial total energy − source release ≈ 0.
```

The JSON field `scenario_validation` records each boolean check, milestone
time, and tolerance. A failed check stops the example rather than presenting
its output as a successful instance of the intended scenario.

## Staged channel-block to 2D impulse handoff

The handoff is expressed through the reusable experiment-recipe primitives in
[`EXPERIMENT_RECIPES.md`](EXPERIMENT_RECIPES.md): an explicit material-ID map,
an ordered material schedule, and a normalized weighted field coupling. The
geometry and timing are recipe inputs, not scalar-wave solver branches.

`run_channel_block_impulsive_event.py` connects the two generic demonstrations
in sequence. First, the three-dimensional channel-block run reaches its final
loss-insert depth and thermal-exchange state. The final fields are then reduced
along the channel axis to form two-dimensional normalized maps:

```text
A(x, y) = mean_z [material is reactive medium]
C(x, y) = mean_z [material is open channel or loss insert]
a_bar(x, y) = mean_z a(x, y, z)
T_bar(x, y) = mean_z T(x, y, z)
```

The Euler event's allowed source profile is a state-derived handoff, not a
direct transfer of pressure or material parameters:

```text
s_event(x, y) = G(x, y) A(x, y)
                [0.25 + 0.45 a_bar/max(a_bar) + 0.30 T_bar/max(T_bar)]
```

where `G` is a centered Gaussian impulse envelope. The 2D Euler continuum then
starts from uniform density and pressure and evolves its own source, pressure,
velocity, and phase fields. Thus the settled channel/rod layout shapes where
the event can grow, but it does not claim that the scalar-wave material labels
are an equation of state or that either solver is calibrated to a specific
physical system.

## Full 3D perforated-block event handoff

`run_perforated_block_3d_event.py` keeps the full three-dimensional precursor
grid for both stages. After the scheduled material exchange has completed, the
same-grid localized event permission is

```text
s(x, y, z) = normalize{ G(x, y, z) A(x, y, z)
  [0.25 + 0.35 a/max(a) + 0.25 T/max(T) + 0.15 p_w/max(p_w)] },
```

where `G` is a user-positioned Gaussian footprint, `A` is the settled active
material indicator, `a` is scalar activity, `T` is scalar heat, and `p_w` is
the scalar-wave energy-pressure proxy. A small normalized thermal offset also
sets the Euler initial pressure:

```text
p_E(x, y, z, 0) = 1 + 0.04 T(x, y, z) / max(T).
```

At the configured event time, the finite Euler source is enabled. The Euler
state then evolves its own equation-of-state pressure, temperature `p_E/rho`,
velocity, and irreversible phase fraction. The scalar `p_w` remains a
precursor diagnostic; it is not represented as thermodynamic pressure. This is
a one-way staged coupling on a common 3D mesh, not a claim that the two models
share a calibrated equation of state or material database.

The driver validates finite and bounded fields, delayed-event activation,
pressure formation, material motion, phase transition, and event → pressure →
phase ordering. Its animation uses the plane through the event-permission
maximum, so the off-center response remains visible.

## Channel-block geometry and insertion schedule

The channel-block layout uses an active cube with half-width `0.82 H`, surrounded by a
high-impedance shell. Six channel centers are distributed across `x` and four across `y`;
each channel is a cylindrical open region extending along `z`.

For start time `t_s`, end time `t_e`, and final depth `f_max`, the insertion fraction is:

```text
f_r(t) = f_max clamp((t - t_s) / (t_e - t_s), 0, 1)
```

The inserted portion occupies the positive-z end of each channel. At `f_max = 0.5`, the
loss insert reaches the channel midpoint. The remaining half stays an open channel, making
the final geometry directly visible in the axial and longitudinal plots.

## Numerical method

The implementation uses:

1. conservative variable-coefficient face fluxes with harmonic face means;
2. Strang splitting between local source/wave dynamics and activity/heat diffusion;
3. explicit midpoint (RK2) integration for local terms;
4. optional matrix-free Crank–Nicolson diffusion for stiff grids;
5. an explicit CFL limit for scalar-wave propagation;
6. trapezoidal integration for history-level source, sink, and energy budgets.

The combination preserves constant fields under pure diffusion, keeps interface fluxes
conservative, and keeps all reported quantities tied to a clearly named normalized term.
