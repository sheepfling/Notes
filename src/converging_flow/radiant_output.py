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
        payload.update(
            {
                "frame_time": np.array([frame.time for frame in result.frames]),
                "frame_activity": np.stack(
                    [frame.activity for frame in result.frames]
                ),
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

    np.savez_compressed(output_directory / "radiant_wave_state.npz", **payload)
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
            "diagnostic, not electromagnetic radiation pressure"
        ),
        "config": asdict(result.config),
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
        },
        "initial": asdict(result.initial_diagnostics),
        "final": asdict(result.final_diagnostics),
        "final_budget": asdict(final_budget),
        "absorber_inserted": result.absorber_inserted,
        "absorber_insertion_time": result.config.absorber_insertion_time,
        "visualization_frames": len(result.frames),
    }
    (output_directory / "radiant_wave_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
####
