# Reusable Experiment Recipes

The numerical kernels advance fields. A recipe supplies the spatial material
map, time-dependent material changes, optional inter-solver field coupling, and
the visualizations or outcome checks to request. This keeps a new experiment
from becoming a new solver branch.

## Building blocks

- `converging_flow.geometry.perforated_block_masks` creates a normalized
  Cartesian block, axial passages, and a 0-to-1 insertion-rank field. Its
  passage counts and proportions are parameters rather than solver settings.
- `converging_flow.material_events.LinearRamp` describes a time fraction.
- `MaterialReplacementEvent` changes a ranked portion of a region into a target
  material. A zero rank across a mask is a whole-region switch; an axial rank
  gives progressive insertion.
- `MaterialPropertyRamp` adds a non-negative, non-compounding offset to one
  material property in a region. Use a material replacement when a property
  needs to decrease.
- `MaterialEventSchedule` groups these changes and can be consumed by any
  solver that owns material fields.
- `NormalizedWeightedCoupling` maps same-shaped fields from one stage into a
  normalized target permission field for another stage.

The scalar-wave solver accepts an explicit `initial_material_ids` field plus a
`material_events` schedule. Its historical layout and insertion arguments are
still accepted for compatibility, but new recipes should use the explicit
fields and schedule.

## Minimal pattern

```python
schedule = MaterialEventSchedule(
    replacements=(
        MaterialReplacementEvent(
            name="ordered material change",
            target_material_id=target_id,
            region=region_mask,
            rank=insertion_rank,
            ramp=LinearRamp(start_time=0.05, end_time=0.12, final_fraction=0.5),
        ),
    ),
)

config = RadiantWaveConfig(
    dimensions=3,
    resolution=(48, 48, 48),
    initial_material_ids=initial_material_ids,
    material_events=schedule,
)
```

For a staged run, reduce or sample the first solver's output to fields with a
common target shape, then apply a coupling:

```python
permission = NormalizedWeightedCoupling(
    weights=(("activity", 0.45), ("heat", 0.30)),
    baseline=0.25,
).apply({"activity": activity, "heat": heat}, envelope=event_footprint)
```

This is a normalized transformation, not a material calibration. A recipe must
document the equation, units, and validation conditions whenever it makes a
claim beyond a qualitative visualization.

## Current recipe migrations

- [`EXPERIMENT_ARCHITECTURE.md`](EXPERIMENT_ARCHITECTURE.md) defines the shared
  geometry → recipe → runtime → driver contract used by every maintained
  example.
- `open_shell_relaxation_config` constructs the former open shell directly
  from an explicit spherical material map and a right-half replacement event;
  it does not depend on a named solver insertion mode.
- `asymmetric_shell_config` constructs the gallery shell from explicit
  reflector, active-medium, and loss-material IDs.
- `run_channel_block_regulation.py` constructs its initial material IDs with
  the geometry helper and schedules axial loss-material replacement plus a
  thermal-loss property ramp.
- `run_channel_block_impulsive_event.py` uses the same precursor recipe, then
  applies `NormalizedWeightedCoupling` to form the 2D source-permission field.
- `perforated_block_regulation_config` is the shared recipe factory used by the
  regulation, 2D handoff, and full-3D event drivers, so their initial material
  map and timed material changes cannot drift apart.
- `ArtifactPlan`, `capture_times`, and `write_summary` provide the common
  artifact directory, animation sampling, and JSON-summary contract across the
  scalar-wave, reactive-Euler, phase-Euler, and staged examples.

Generated scalar-wave summaries include the shape and IDs of the initial map,
event names, target material IDs, region cell counts, ramps, final event
progress, and per-frame event progress. This makes a run reproducible without
serializing bulky spatial masks into JSON.
