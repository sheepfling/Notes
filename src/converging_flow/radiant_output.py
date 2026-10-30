from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from converging_flow.radiant_wave import (
    RadiantWaveResult,
    interface_reflection_coefficient,
    radiant_wave_budget,
)


def _config_summary(result: RadiantWaveResult) -> dict[str, object]:
    """Return JSON-safe configuration metadata without serializing field arrays."""
    config = asdict(result.config)
    initial_ids = result.config.initial_material_ids
    config["initial_material_ids"] = (
        None
        if initial_ids is None
        else {
            "shape": list(initial_ids.shape),
            "material_ids": [int(value) for value in np.unique(initial_ids)],
        }
    )
    config["material_events"] = {
        "replacements": [
            {
                "name": event.name,
                "target_material_id": event.target_material_id,
                "region_cell_count": int(np.count_nonzero(event.region)),
                "ramp": asdict(event.ramp),
            }
            for event in result.config.material_events.replacements
        ],
        "property_ramps": [
            {
                "name": event.name,
                "property_name": event.property_name,
                "region_cell_count": int(np.count_nonzero(event.region)),
                "amplitude": event.amplitude,
                "ramp": asdict(event.ramp),
            }
            for event in result.config.material_events.property_ramps
        ],
    }
    return config
####
def save_radiant_wave_result(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "activity": result.activity,
        "heat": result.heat,
        "wave": result.wave,
        "wave_velocity": result.wave_velocity,
        "wave_energy": result.wave_energy,
        "wave_pressure": result.wave_pressure,
        "force_magnitude": result.force_magnitude,
        "material_id": result.materials.material_id,
        "activity_diffusivity": result.materials.activity_diffusivity,
        "growth_rate": result.materials.growth_rate,
        "loss_rate": result.materials.loss_rate,
        "thermal_conductivity": result.materials.thermal_conductivity,
        "heat_capacity": result.materials.heat_capacity,
        "heat_loss_rate": result.materials.heat_loss_rate,
        "wave_density": result.materials.wave_density,
        "wave_stiffness": result.materials.wave_stiffness,
        "wave_damping": result.materials.wave_damping,
        "time": np.array(result.time),
        "steps": np.array(result.steps),
    }
    for axis, coordinate in enumerate(result.coordinates):
        payload[f"coordinate_{axis}"] = coordinate
    ####

    if result.frames:
        frame_time = np.array([frame.time for frame in result.frames])
        frame_source = np.array(
            [frame.budget.source_strength for frame in result.frames]
        )
        frame_sink = np.array([frame.budget.sink_strength for frame in result.frames])
        cumulative_source = np.concatenate(
            (
                [0.0],
                np.cumsum(
                    np.diff(frame_time) * (frame_source[:-1] + frame_source[1:]) / 2.0
                ),
            )
        )
        cumulative_sink = np.concatenate(
            (
                [0.0],
                np.cumsum(
                    np.diff(frame_time) * (frame_sink[:-1] + frame_sink[1:]) / 2.0
                ),
            )
        )
        payload.update(
            {
                "frame_time": frame_time,
                "frame_activity": np.stack([frame.activity for frame in result.frames]),
                "frame_heat": np.stack([frame.heat for frame in result.frames]),
                "frame_wave": np.stack([frame.wave for frame in result.frames]),
                "frame_wave_velocity": np.stack(
                    [frame.wave_velocity for frame in result.frames]
                ),
                "frame_wave_energy": np.stack(
                    [frame.wave_energy for frame in result.frames]
                ),
                "frame_wave_pressure": np.stack(
                    [frame.wave_pressure for frame in result.frames]
                ),
                "frame_material_id": np.stack(
                    [frame.material_id for frame in result.frames]
                ),
                "frame_absorber_inserted": np.array(
                    [frame.absorber_inserted for frame in result.frames]
                ),
                "frame_absorber_fraction": np.array(
                    [frame.absorber_fraction for frame in result.frames]
                ),
                # Generic aliases for consumers that do not use the historical
                # ``absorber`` terminology retained above for compatibility.
                "frame_loss_inserted": np.array(
                    [frame.absorber_inserted for frame in result.frames]
                ),
                "frame_loss_insert_fraction": np.array(
                    [frame.absorber_fraction for frame in result.frames]
                ),
                "material_event_names": np.asarray(result.material_event_names),
                "frame_material_event_progress": np.asarray(
                    [frame.material_event_progress for frame in result.frames],
                    dtype=np.float64,
                ),
                "frame_total_activity": np.array(
                    [frame.budget.total_activity for frame in result.frames]
                ),
                "frame_thermal_energy": np.array(
                    [frame.budget.thermal_energy for frame in result.frames]
                ),
                "frame_total_wave_energy": np.array(
                    [frame.budget.total_wave_energy for frame in result.frames]
                ),
                "frame_source_strength": np.array(
                    [frame.budget.source_strength for frame in result.frames]
                ),
                "frame_sink_strength": np.array(
                    [frame.budget.sink_strength for frame in result.frames]
                ),
                "frame_balance_factor": np.array(
                    [frame.budget.balance_factor for frame in result.frames]
                ),
                "frame_autocatalytic_activity_rate": np.array(
                    [
                        frame.budget.autocatalytic_activity_rate
                        for frame in result.frames
                    ]
                ),
                "frame_thermal_feedback_activity_rate": np.array(
                    [
                        frame.budget.thermal_feedback_activity_rate
                        for frame in result.frames
                    ]
                ),
                "frame_wave_feedback_activity_rate": np.array(
                    [
                        frame.budget.wave_feedback_activity_rate
                        for frame in result.frames
                    ]
                ),
                "frame_activity_loss_rate": np.array(
                    [frame.budget.activity_loss_rate for frame in result.frames]
                ),
                "frame_heat_source_power": np.array(
                    [frame.budget.heat_source_power for frame in result.frames]
                ),
                "frame_heat_loss_power": np.array(
                    [frame.budget.heat_loss_power for frame in result.frames]
                ),
                "frame_wave_source_power": np.array(
                    [frame.budget.wave_source_power for frame in result.frames]
                ),
                "frame_wave_dissipation_power": np.array(
                    [frame.budget.wave_dissipation_power for frame in result.frames]
                ),
                "frame_cumulative_source": cumulative_source,
                "frame_cumulative_sink": cumulative_sink,
                "frame_cumulative_net_source_minus_sink": (
                    cumulative_source - cumulative_sink
                ),
                "frame_material_wave_energy": np.array(
                    [frame.budget.material_wave_energy for frame in result.frames]
                ),
                "frame_material_wave_dissipation_power": np.array(
                    [
                        frame.budget.material_wave_dissipation_power
                        for frame in result.frames
                    ]
                ),
            }
        )
    ####

    # NumPy accepts arbitrary archive keys; its static signature cannot express
    # an unpacked mapping without treating every key as a named option.
    np.savez_compressed(
        output_directory / "radiant_wave_state.npz",
        **payload,  # pyright: ignore[reportArgumentType]
    )
    final_budget = radiant_wave_budget(
        result.activity,
        result.heat,
        result.wave_velocity,
        result.wave_energy,
        result.wave_pressure,
        result.materials,
        result.config,
    )
    summary = {
        "model": (
            "normalized heterogeneous autocatalytic reaction-diffusion, "
            "heat diffusion, and damped scalar wave"
        ),
        "pressure_note": (
            "wave_pressure is a normalized scalar-wave energy-pressure "
            "diagnostic, not mechanical pressure"
        ),
        "config": _config_summary(result),
        "resolved_backend": result.resolved_backend,
        "resolved_diffusion_method": result.resolved_diffusion_method,
        "interface_reflection_coefficients": {
            "neutral_to_reflector": interface_reflection_coefficient(
                result.config.neutral,
                result.config.reflector,
            ),
            "neutral_to_absorber": interface_reflection_coefficient(
                result.config.neutral,
                result.config.absorber,
            ),
            "neutral_to_loss_insert": interface_reflection_coefficient(
                result.config.neutral,
                result.config.absorber,
            ),
        },
        "initial": asdict(result.initial_diagnostics),
        "final": asdict(result.final_diagnostics),
        "final_budget": asdict(final_budget),
        "absorber_inserted": result.absorber_inserted,
        "absorber_fraction": result.absorber_fraction,
        "absorber_insertion_time": result.config.absorber_insertion_time,
        "loss_inserted": result.absorber_inserted,
        "loss_insert_fraction": result.absorber_fraction,
        "loss_insert_start_time": result.config.absorber_insertion_time,
        "material_events": {
            name: progress
            for name, progress in zip(
                result.material_event_names,
                result.material_event_progress,
                strict=True,
            )
        },
        "visualization_frames": len(result.frames),
    }
    if result.frames:
        frame_time = np.array([frame.time for frame in result.frames])
        frame_inserted = np.array([frame.absorber_inserted for frame in result.frames])
        if np.any(frame_inserted) and np.any(~frame_inserted):
            insertion_index = int(np.flatnonzero(frame_inserted)[0])
            budgets = [frame.budget for frame in result.frames]
            cumulative_net = np.asarray(
                payload["frame_cumulative_net_source_minus_sink"]
            )
            summary["phase_analysis"] = {
                "initial_time": float(frame_time[0]),
                "insertion_time": float(frame_time[insertion_index]),
                "final_time": float(frame_time[-1]),
                "pre_insertion_balance_max": float(
                    max(budget.balance_factor for budget in budgets[:insertion_index])
                ),
                "first_post_insertion_balance": float(
                    budgets[insertion_index].balance_factor
                ),
                "post_insertion_balance_final": float(budgets[-1].balance_factor),
                "thermal_energy_pre_insertion": float(
                    budgets[insertion_index - 1].thermal_energy
                ),
                "thermal_energy_first_post_insertion": float(
                    budgets[insertion_index].thermal_energy
                ),
                "thermal_energy_final": float(budgets[-1].thermal_energy),
                "cumulative_net_source_minus_sink_at_insertion": float(
                    cumulative_net[insertion_index]
                ),
                "cumulative_net_source_minus_sink_final": float(cumulative_net[-1]),
                "interpretation": (
                    "The balance factor describes instantaneous normalized source-to-sink "
                    "rates. Cumulative net source-minus-sink and stored thermal/wave state "
                    "must be inspected separately; neither is a conserved physical energy."
                ),
            }
        ####
    ####
    (output_directory / "radiant_wave_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
####
