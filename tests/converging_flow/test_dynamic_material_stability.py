"""Stability checks for material changes during a radiant-wave run."""

from dataclasses import replace

import numpy as np
import pytest

from converging_flow import radiant_wave
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
    stable_timestep,
)


def test_stiffness_ramp_stays_close_to_small_step_reference() -> None:
    event = MaterialPropertyRamp(
        name="stiffness",
        property_name="wave_stiffness",
        region=np.ones(16, dtype=bool),
        amplitude=1e5,
        ramp=LinearRamp(0.01, 0.02),
    )
    config = RadiantWaveConfig(
        dimensions=1,
        resolution=(16,),
        backend="numpy",
        final_time=0.06,
        maximum_timestep=0.002,
        material_events=MaterialEventSchedule(property_ramps=(event,)),
        diffusion_method="explicit",
    )
    result = run_radiant_wave(config)
    reference = run_radiant_wave(replace(config, maximum_timestep=0.00005))

    assert result.steps > 30
    assert np.max(np.abs(result.wave)) < 1e-3
    assert np.max(np.abs(result.wave - reference.wave)) < 0.3 * np.max(np.abs(reference.wave))
####


@pytest.mark.parametrize("start", [0.0, 0.01])
@pytest.mark.parametrize("method", ["explicit", "crank-nicolson"])
def test_stiff_replacement_recalculates_bound_and_applies_at_zero(
    start: float, method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    region = np.ones(16, dtype=bool)
    event = MaterialReplacementEvent(
        name="replace",
        target_material_id=int(ABSORBER_ID),
        region=region,
        rank=np.zeros(16),
        ramp=LinearRamp(start, start),
    )
    base = RadiantWaveConfig(dimensions=1, resolution=(16,))
    config = replace(
        base,
        initial_material_ids=np.full(16, NEUTRAL_ID, dtype=np.int8),
        absorber=replace(base.absorber, wave_stiffness=1e5),
        final_time=0.012,
        maximum_timestep=0.002,
        diffusion_method=method,
        material_events=MaterialEventSchedule(replacements=(event,)),
    )
    original = radiant_wave._advance_fields_backend
    checked: list[float] = []

    def advance(activity, heat, wave, velocity, materials, config, timestep, backend, method):
        current = radiant_wave._numpy_material_fields(materials, backend)
        assert timestep <= stable_timestep(config, current, method) + 1e-14
        if np.all(current.material_id == ABSORBER_ID):
            checked.append(timestep)
        ####
        return original(activity, heat, wave, velocity, materials, config, timestep, backend, method)
    ####

    monkeypatch.setattr(radiant_wave, "_advance_fields_backend", advance)
    result = run_radiant_wave(config, snapshot_count=2)
    assert checked
    assert max(checked) < config.maximum_timestep
    if start == 0.0:
        assert np.all(result.frames[0].material_id == ABSORBER_ID)
    ####
####


def test_auto_diffusion_method_tracks_ramp(monkeypatch: pytest.MonkeyPatch) -> None:
    event = MaterialPropertyRamp(
        name="diffusion",
        property_name="activity_diffusivity",
        region=np.ones(16, dtype=bool),
        amplitude=100.0,
        ramp=LinearRamp(0.001, 0.002),
    )
    config = RadiantWaveConfig(
        dimensions=1,
        resolution=(16,),
        final_time=0.004,
        maximum_timestep=0.0005,
        diffusion_method="auto",
        material_events=MaterialEventSchedule(property_ramps=(event,)),
    )
    original = radiant_wave._advance_fields_backend
    methods: list[str] = []

    def advance(activity, heat, wave, velocity, materials, config, timestep, backend, method):
        current = radiant_wave._numpy_material_fields(materials, backend)
        assert timestep <= stable_timestep(config, current, method) + 1e-14
        methods.append(method)
        return original(activity, heat, wave, velocity, materials, config, timestep, backend, method)
    ####

    monkeypatch.setattr(radiant_wave, "_advance_fields_backend", advance)
    result = run_radiant_wave(config)
    assert methods[0] == "explicit"
    assert "crank-nicolson" in methods
    assert result.resolved_diffusion_method == methods[-1]
####


@pytest.mark.parametrize("control", ["absorber", "rod"])
def test_replacement_cannot_mix_with_legacy_insertion(control: str) -> None:
    event = MaterialReplacementEvent(
        name="replace",
        target_material_id=int(ABSORBER_ID),
        region=np.ones((8, 8, 8), dtype=bool),
        rank=np.zeros((8, 8, 8)),
        ramp=LinearRamp(0.0, 0.0),
    )
    controls = (
        {"absorber_insertion_time": 0.005}
        if control == "absorber"
        else {
            "material_layout": "channel-block",
            "rod_insertion_start_time": 0.002,
            "rod_insertion_end_time": 0.008,
        }
    )
    with pytest.raises(ValueError, match="do not mix material_events"):
        RadiantWaveConfig(
            dimensions=3,
            resolution=(8, 8, 8),
            final_time=0.01,
            material_events=MaterialEventSchedule(replacements=(event,)),
            **controls,
        )
    ####
####


def test_property_ramp_does_not_suppress_legacy_absorber() -> None:
    event = MaterialPropertyRamp(
        name="loss",
        property_name="heat_loss_rate",
        region=np.ones(16, dtype=bool),
        amplitude=0.5,
        ramp=LinearRamp(0.0, 0.004),
    )
    config = RadiantWaveConfig(
        dimensions=1,
        resolution=(16,),
        final_time=0.01,
        absorber_insertion_time=0.005,
        material_events=MaterialEventSchedule(property_ramps=(event,)),
    )
    result = run_radiant_wave(config)
    assert result.absorber_inserted
    assert np.any(result.materials.material_id == ABSORBER_ID)
####
