from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from converging_flow.euler import conservative_to_primitive
from converging_flow.experiment import SimulationResult, radial_profile_data


def save_result(result: SimulationResult, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    density, velocity, pressure = conservative_to_primitive(
        result.state,
        result.config.gamma,
        result.config.density_floor,
        result.config.pressure_floor,
    )
    profile = radial_profile_data(result)

    payload: dict[str, object] = {
        "state": result.state,
        "density": density,
        "velocity": velocity,
        "pressure": pressure,
        "time": np.array(result.time),
        "steps": np.array(result.steps),
        "radial_radius": profile.radius,
        "radial_density": profile.density,
        "radial_pressure": profile.pressure,
        "radial_speed": profile.speed,
        "radial_velocity": profile.radial_velocity,
        "radial_mach": profile.mach,
        "radial_density_standard_deviation": profile.density_standard_deviation,
        "radial_pressure_standard_deviation": profile.pressure_standard_deviation,
    }
    for axis, coordinate in enumerate(result.coordinates):
        payload[f"coordinate_{axis}"] = coordinate
    ####

    if result.frames:
        payload.update(
            {
                "frame_time": np.array([frame.time for frame in result.frames]),
                "frame_density": np.stack(
                    [frame.density_field for frame in result.frames]
                ),
                "frame_pressure": np.stack(
                    [frame.pressure_field for frame in result.frames]
                ),
                "frame_speed": np.stack([frame.speed_field for frame in result.frames]),
                "frame_radial_velocity_field": np.stack(
                    [frame.radial_velocity_field for frame in result.frames]
                ),
                "frame_radial_radius": np.stack(
                    [frame.radial_profile.radius for frame in result.frames]
                ),
                "frame_radial_density": np.stack(
                    [frame.radial_profile.density for frame in result.frames]
                ),
                "frame_radial_pressure": np.stack(
                    [frame.radial_profile.pressure for frame in result.frames]
                ),
                "frame_radial_speed": np.stack(
                    [frame.radial_profile.speed for frame in result.frames]
                ),
                "frame_radial_velocity": np.stack(
                    [frame.radial_profile.radial_velocity for frame in result.frames]
                ),
                "frame_radial_mach": np.stack(
                    [frame.radial_profile.mach for frame in result.frames]
                ),
                "frame_radial_density_standard_deviation": np.stack(
                    [
                        frame.radial_profile.density_standard_deviation
                        for frame in result.frames
                    ]
                ),
                "frame_radial_pressure_standard_deviation": np.stack(
                    [
                        frame.radial_profile.pressure_standard_deviation
                        for frame in result.frames
                    ]
                ),
            }
        )
    ####

    np.savez_compressed(output_directory / "state.npz", **payload)

    summary = {
        "config": asdict(result.config),
        "resolved_backend": result.resolved_backend,
        "initial": asdict(result.initial_diagnostics),
        "final": asdict(result.final_diagnostics),
        "visualization_frames": len(result.frames),
        "relative_mass_change": (
            result.final_diagnostics.mass / result.initial_diagnostics.mass - 1.0
        ),
        "relative_energy_change": (
            result.final_diagnostics.total_energy
            / result.initial_diagnostics.total_energy
            - 1.0
        ),
    }
    (output_directory / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
####
