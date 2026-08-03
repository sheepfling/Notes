from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from converging_flow.radiant_output import save_radiant_wave_result
from converging_flow.radiant_plotting import (
    save_radiant_wave_animations,
    save_radiant_wave_plots,
)
from converging_flow.radiant_wave import (
    ABSORBER_ID,
    NEUTRAL_ID,
    REFLECTOR_ID,
    RadiantWaveConfig,
    conservative_flux_divergence,
    initialize_fields,
    interface_reflection_coefficient,
    run_radiant_wave,
)


@pytest.mark.parametrize("dimensions", [1, 2, 3])
def test_constant_field_has_zero_variable_coefficient_divergence(
    dimensions: int,
) -> None:
    shape = (12,) * dimensions
    values = np.full(shape, 2.5, dtype=np.float64)
    coefficient = np.linspace(0.5, 2.0, values.size).reshape(shape)

    result = conservative_flux_divergence(
        values,
        coefficient,
        (0.1,) * dimensions,
    )

    assert np.allclose(result, 0.0)
####


def test_zero_flux_operator_is_globally_conservative() -> None:
    rng = np.random.default_rng(42)
    values = rng.normal(size=(18, 14))
    coefficient = np.exp(rng.normal(scale=0.4, size=values.shape))

    result = conservative_flux_divergence(values, coefficient, (0.2, 0.3))

    assert float(np.sum(result)) == pytest.approx(0.0, abs=1.0e-12)
####


def test_asymmetric_material_map_and_impedance_behavior() -> None:
    config = RadiantWaveConfig(
        dimensions=1,
        resolution=(40,),
        neutral_half_width=0.10,
    )
    _coordinates, materials, *_fields = initialize_fields(config)

    assert np.all(materials.material_id[:18] == REFLECTOR_ID)
    assert np.any(materials.material_id == NEUTRAL_ID)
    assert np.all(materials.material_id[-18:] == ABSORBER_ID)

    neutral_to_reflector = interface_reflection_coefficient(
        config.neutral,
        config.reflector,
    )
    neutral_to_absorber = interface_reflection_coefficient(
        config.neutral,
        config.absorber,
    )
    assert neutral_to_reflector == pytest.approx(0.6)
    assert neutral_to_absorber == pytest.approx(0.0)
    assert config.absorber.wave_damping > config.neutral.wave_damping
####


def test_spherical_shell_layout_has_asymmetric_shell_and_inclusions() -> None:
    config = RadiantWaveConfig(
        dimensions=3,
        resolution=(24, 24, 24),
        material_layout="spherical-shell",
    )
    coordinates, materials, *_fields = initialize_fields(config)

    assert set(np.unique(materials.material_id)) == {
        int(REFLECTOR_ID),
        int(NEUTRAL_ID),
        int(ABSORBER_ID),
    }
    midpoint = config.resolution[1] // 2
    assert materials.material_id[1, midpoint, midpoint] == REFLECTOR_ID
    assert materials.material_id[-2, midpoint, midpoint] == ABSORBER_ID
    assert np.count_nonzero(materials.material_id == ABSORBER_ID) > 0
    assert coordinates[0].shape == (config.resolution[0],)
####


def test_spherical_shell_layout_requires_three_dimensions() -> None:
    with pytest.raises(ValueError, match="requires 3D"):
        RadiantWaveConfig(
            dimensions=2,
            resolution=(16, 16),
            material_layout="spherical-shell",
        )
####


def test_absorber_insertion_changes_materials_and_frame_state() -> None:
    config = RadiantWaveConfig(
        dimensions=3,
        resolution=(10, 10, 10),
        final_time=0.01,
        material_layout="spherical-shell-open",
        absorber_insertion_time=0.005,
    )
    result = run_radiant_wave(config, snapshot_count=3)

    assert result.absorber_inserted
    assert [frame.absorber_inserted for frame in result.frames] == [
        False,
        True,
        True,
    ]
    assert np.all(result.materials.material_id[7:, :, :] == ABSORBER_ID)
####


@pytest.mark.parametrize("dimensions,resolution", [(1, 64), (2, 28), (3, 14)])
def test_radiant_wave_fields_remain_finite_and_bounded(
    dimensions: int,
    resolution: int,
) -> None:
    config = RadiantWaveConfig(
        dimensions=dimensions,  # type: ignore[arg-type]
        resolution=(resolution,) * dimensions,
        final_time=0.04,
    )

    result = run_radiant_wave(config, snapshot_count=3)

    assert result.time == pytest.approx(config.final_time)
    assert len(result.frames) == 3
    assert np.all(np.isfinite(result.activity))
    assert np.all(np.isfinite(result.heat))
    assert np.all(np.isfinite(result.wave))
    assert np.all(np.isfinite(result.wave_pressure))
    assert np.all((0.0 <= result.activity) & (result.activity <= 1.0))
    assert np.all(result.heat >= 0.0)
    assert np.all(result.wave_energy >= 0.0)
    assert np.all(result.wave_pressure >= 0.0)
    assert np.all(result.force_magnitude >= 0.0)
    assert all(np.isfinite(frame.budget.balance_factor) for frame in result.frames)
    assert all(frame.budget.source_strength >= 0.0 for frame in result.frames)
    assert all(frame.budget.sink_strength >= 0.0 for frame in result.frames)
####


def test_radiant_wave_output_and_visualizations(tmp_path: Path) -> None:
    config = RadiantWaveConfig(
        dimensions=2,
        resolution=(24, 24),
        final_time=0.02,
    )
    result = run_radiant_wave(config, snapshot_count=3)

    save_radiant_wave_result(result, tmp_path)
    save_radiant_wave_plots(result, tmp_path)
    save_radiant_wave_animations(result, tmp_path, fps=4)

    with np.load(tmp_path / "radiant_wave_state.npz") as payload:
        assert payload["activity"].shape == (24, 24)
        assert payload["material_id"].shape == (24, 24)
        assert payload["frame_wave_pressure"].shape == (3, 24, 24)
        assert payload["frame_balance_factor"].shape == (3,)
    ####

    assert (tmp_path / "radiant_wave_summary.json").is_file()
    assert (tmp_path / "materials.png").is_file()
    assert (tmp_path / "wave_pressure.png").is_file()
    assert (tmp_path / "balance_factor_history.png").is_file()
    assert (tmp_path / "wave_pressure_evolution.gif").is_file()
####
