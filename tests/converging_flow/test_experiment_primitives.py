from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from converging_flow.coupling import NormalizedWeightedCoupling
from converging_flow.example_runtime import ArtifactPlan, capture_times, write_summary
from converging_flow.geometry import (
    axial_half_mask,
    perforated_block_masks,
    spherical_shell_mask,
)
from converging_flow.material_events import (
    LinearRamp,
    MaterialEventSchedule,
    MaterialPropertyRamp,
    MaterialReplacementEvent,
)
from converging_flow.radiant_wave import (
    ABSORBER_ID,
    NEUTRAL_ID,
    RadiantWaveConfig,
    run_radiant_wave,
)
from converging_flow.recipes import (
    PhaseThermalParameters,
    asymmetric_shell_config,
    open_shell_relaxation_config,
    perforated_block_event_parameters_from_file,
    perforated_block_parameters_from_json,
    perforated_block_regulation_config,
)


def test_ranked_material_event_and_property_ramp_are_solver_driven() -> None:
    resolution = 32
    initial_material_ids = np.full(resolution, NEUTRAL_ID, dtype=np.int8)
    region = np.ones(resolution, dtype=bool)
    rank = np.linspace(0.0, 1.0, resolution, dtype=np.float64)
    ramp = LinearRamp(0.004, 0.008, 0.50)
    # A non-empty, disjoint property region keeps the property event valid while
    # isolating this test to the ranked material replacement.
    property_region = np.zeros(resolution, dtype=bool)
    property_region[-1] = True
    schedule = MaterialEventSchedule(
        replacements=(
            MaterialReplacementEvent(
                name="ranked loss replacement",
                target_material_id=int(ABSORBER_ID),
                region=region,
                rank=rank,
                ramp=ramp,
            ),
        ),
        property_ramps=(
            MaterialPropertyRamp(
                name="thermal-loss offset",
                property_name="heat_loss_rate",
                region=property_region,
                amplitude=0.5,
                ramp=ramp,
            ),
        ),
    )
    config = RadiantWaveConfig(
        dimensions=1,
        resolution=(resolution,),
        final_time=0.012,
        initial_material_ids=initial_material_ids,
        material_events=schedule,
    )

    result = run_radiant_wave(config, snapshot_count=4)

    replaced = rank <= 0.50
    assert np.array_equal(result.materials.material_id == ABSORBER_ID, replaced)
    assert result.material_event_names == ("ranked loss replacement",)
    assert result.material_event_progress == (0.50,)
    assert result.frames[-1].material_event_progress == (0.50,)
    assert result.materials.heat_loss_rate[-1] == pytest.approx(
        config.neutral.heat_loss_rate + 0.5 * ramp.final_fraction
    )
####


def test_perforated_geometry_exposes_ordered_passages() -> None:
    coordinate = np.linspace(-0.95, 0.95, 40, dtype=np.float64)
    boundary, passages, rank = perforated_block_masks(
        (coordinate, coordinate, coordinate),
        half_extent=1.0,
        channel_counts=(3, 2),
    )

    assert boundary.shape == (40, 40, 40)
    assert np.any(boundary)
    assert np.any(passages)
    assert float(np.min(rank[passages])) >= 0.0
    assert float(np.max(rank[passages])) <= 1.0
    occupied_slices = np.flatnonzero(np.any(passages, axis=(0, 1)))
    assert occupied_slices.size > 1
    assert rank[0, 0, occupied_slices[0]] > rank[0, 0, occupied_slices[-1]]
####


def test_normalized_weighted_coupling_is_bounded_and_envelope_gated() -> None:
    activity = np.array([[0.0, 2.0], [1.0, 4.0]])
    heat = np.array([[1.0, 0.0], [3.0, 2.0]])
    envelope = np.array([[1.0, 0.0], [1.0, 1.0]])

    result = NormalizedWeightedCoupling(
        weights=(("activity", 0.5), ("heat", 0.5)),
        baseline=0.25,
    ).apply({"activity": activity, "heat": heat}, envelope)

    assert np.all((0.0 <= result) & (result <= 1.0))
    assert result[0, 1] == 0.0
    assert float(np.max(result)) == 1.0
####


def test_shell_recipes_use_explicit_material_fields_and_generic_events() -> None:
    relaxation = open_shell_relaxation_config(
        resolution=16,
        backend="numpy",
        final_time=0.04,
        insertion_time=0.02,
    )
    assert relaxation.initial_material_ids is not None
    assert relaxation.absorber_insertion_time is None
    assert len(relaxation.material_events.replacements) == 1
    event = relaxation.material_events.replacements[0]
    assert event.target_material_id == int(ABSORBER_ID)
    assert np.any(event.region)
    assert np.any(~event.region)

    asymmetric = asymmetric_shell_config(16, "numpy")
    assert asymmetric.initial_material_ids is not None
    assert np.any(asymmetric.initial_material_ids == ABSORBER_ID)
####


def test_common_runtime_and_geometry_primitives(tmp_path: Path) -> None:
    coordinate = np.linspace(-0.9, 0.9, 10, dtype=np.float64)
    shell = spherical_shell_mask((coordinate, coordinate, coordinate), radius=0.6)
    positive_y = axial_half_mask((coordinate, coordinate, coordinate), axis=1)
    assert shell.shape == (10, 10, 10)
    assert positive_y.shape == shell.shape
    assert positive_y[:, 0, :].sum() == 0
    assert positive_y[:, -1, :].all()

    assert np.array_equal(capture_times(0.3, 3), np.array([0.0, 0.15, 0.3]))
    plan = ArtifactPlan(tmp_path / "artifacts", frames=2, fps=8)
    assert plan.output_directory.name == "artifacts"
    write_summary(tmp_path / "summary.json", {"answer": 42})
    assert '"answer": 42' in (tmp_path / "summary.json").read_text(encoding="utf-8")
####


def test_data_driven_recipe_parameters_override_material_and_geometry(
    tmp_path: Path,
) -> None:
    parameter_file = tmp_path / "scenario.json"
    parameter_file.write_text(
        """{
          "resolution": 24,
          "backend": "numpy",
          "channel_counts": [3, 2],
          "materials": {"active_medium": {"specific_heat": 2.5}},
          "source": {"seed_width": 0.21}
        }""",
        encoding="utf-8",
    )
    parameters = perforated_block_parameters_from_json(parameter_file)
    assert parameters.channel_counts == (3, 2)
    assert parameters.materials.active_medium.specific_heat == 2.5
    assert parameters.source.seed_width == 0.21
    config = perforated_block_regulation_config(parameters=parameters)
    assert config.neutral.heat_capacity == 2.5
    assert config.seed_width == 0.21

    phase = PhaseThermalParameters(
        specific_heat=4.0,
        gas_constant=1.0,
        phase_change_energy_per_mass=2.5,
    ).phase_config()
    assert phase.gamma == pytest.approx(1.25)
    assert phase.latent_heat_per_mass == 2.5
####


def test_complete_staged_event_document_loads_all_control_categories(
    tmp_path: Path,
) -> None:
    document = tmp_path / "event.json"
    document.write_text(
        """{
          "precursor": {"resolution": 24, "backend": "numpy"},
          "initial_state": {"pressure": 1.2},
          "event": {"center": [0.1, 0.2, 0.3], "width": 0.2},
          "coupling": {"heat_weight": 0.4},
          "phase": {"specific_heat": 4.0, "phase_change_energy_per_mass": 2.0},
          "numerics": {"cfl": 0.15},
          "validation": {"minimum_speed": 0.08},
          "presentation": {"frames": 9, "fps": 20}
        }""",
        encoding="utf-8",
    )
    parameters = perforated_block_event_parameters_from_file(document)
    assert parameters.precursor.resolution == 24
    assert parameters.initial_state.pressure == 1.2
    assert parameters.event.center == (0.1, 0.2, 0.3)
    assert parameters.coupling.heat_weight == 0.4
    assert parameters.phase.phase_change_energy_per_mass == 2.0
    assert parameters.phase.phase_config().gamma == pytest.approx(1.25)
    assert parameters.numerics.cfl == 0.15
    assert parameters.validation.minimum_speed == 0.08
    assert parameters.presentation.fps == 20
####
