from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from converging_flow.reaction_diffusion import ReactionResult


def save_reaction_result(result: ReactionResult, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "activity": result.activity,
        "heat": result.heat,
        "wave": result.wave,
        "wave_velocity": result.wave_velocity,
        "catalyst": result.catalyst,
        "quencher": result.quencher,
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
            }
        )
    ####

    np.savez_compressed(output_directory / "reaction_state.npz", **payload)
    summary = {
        "model": "generic autocatalytic reaction-diffusion with heat and damped wave",
        "config": asdict(result.config),
        "initial": asdict(result.initial_diagnostics),
        "final": asdict(result.final_diagnostics),
        "visualization_frames": len(result.frames),
    }
    (output_directory / "reaction_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
####
