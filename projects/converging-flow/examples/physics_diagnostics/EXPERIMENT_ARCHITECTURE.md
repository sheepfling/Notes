# Unified Experiment Architecture

Every maintained example follows the same four-layer arrangement. The goal is
to make new scenarios combinations of reusable pieces rather than new solver
branches.

| Layer | Responsibility | Location |
| --- | --- | --- |
| Geometry and events | Spatial masks, material IDs, and timed material changes | `converging_flow.geometry`, `converging_flow.material_events` |
| Recipe | Parameterized initial state and event schedule | `converging_flow.recipes` |
| Runtime | Backend cache, capture schedule, standard result artifacts, JSON summary | `converging_flow.example_runtime` |
| Driver | Command-line options and solver-specific plots or validation | `examples/**` |

`initial_material_ids` and `MaterialEventSchedule` are the standard scalar-wave
scenario interface. Legacy layout and named insertion controls remain
compatible with saved workflows, but maintained examples do not use them to
define new geometry or events.

## Maintained drivers

- `run_absorber_relaxation.py` uses `open_shell_relaxation_config`: an explicit
  shell and a timed right-half loss-material replacement.
- `run_channel_block_regulation.py`, `run_channel_block_impulsive_event.py`,
  and `run_perforated_block_3d_event.py` share
  `perforated_block_regulation_config`.
- `run_gallery.py` uses `asymmetric_shell_config` for its heterogeneous shell,
  then delegates to the standalone pressure demonstration.
- `reactive_pressure_demo.py` and `impulsive_phase_transition_demo.py` share
  capture schedules, summary formatting, and their normalized solver recipe
  parameters.
- `pressure_semantics_comparison.py` is diagnostic-only: it compares the
  saved scalar-wave proxy with EOS-derived pressure and does not advance a
  scenario itself.

The reactive-Euler and phase-Euler equations are deliberately separate from
the scalar-wave equations. They share runtime conventions, not a claim that
their fields are a calibrated common material law. Staged examples label their
normalized handoff explicitly and validate their expected qualitative sequence.

## Adjusting a scenario

The scalar-wave recipes accept typed parameter objects:
`PerforatedBlockParameters`, `ShellRelaxationParameters`,
`RadiantMaterialSet`, and `RadiantSourceParameters`. Every material has its
own activity diffusivity/growth/loss, conductivity, **specific heat**,
heat-loss, wave density/stiffness, and damping. Geometry and numerical values
include extent, resolution, channel count/radius, insertion timing/fraction,
CFL, maximum timestep, and final time. `ArtifactPlan` independently defines
capture count and FPS.

The two scalar-wave drivers also accept complete JSON documents with
`--parameters`; the checked-in defaults are in
[`parameter_sets`](parameter_sets). For example:

```
python examples/physics_diagnostics/run_channel_block_regulation.py --parameters examples/physics_diagnostics/parameter_sets/perforated_block_default.json --frames 181 --fps 24
```

`PhaseThermalParameters` supplies specific heat, gas constant, released energy
per mass, source growth, phase-change energy per mass (latent heat), transition
temperature/width, and relaxation time to phase-Euler recipes. The ideal-gas
constraint is `gamma = 1 + R / c_v`; the default normalized values retain the
previous `gamma = 1.4` behavior.

The standalone reactive-pressure and impulsive-phase drivers expose those
thermal controls as CLI flags (`--specific-heat`, `--gas-constant`,
`--heat-release-per-mass`, and, for the phase example,
`--phase-change-energy-per-mass` plus transition controls). Their summaries
include the complete resolved thermal model.

The full 3D staged experiment uses
[`parameter_sets/perforated_block_3d_event_default.json`](parameter_sets/perforated_block_3d_event_default.json).
It is the complete document form: `precursor`, `initial_state`, `event`,
`coupling`, `phase`, `numerics`, `validation`, and `presentation`.

```
python examples/physics_diagnostics/run_perforated_block_3d_event.py --parameters examples/physics_diagnostics/parameter_sets/perforated_block_3d_event_default.json
```

Use `.json` for portable, dependency-free execution. `.yaml` and `.yml` are
also accepted when `PyYAML` is installed, which permits comments and a less
punctuation-heavy editing experience.
