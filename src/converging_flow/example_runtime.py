"""Shared execution and artifact conventions for maintained examples.

Recipes describe a scenario; drivers select diagnostics.  This module owns the
small amount of operational plumbing common to both: backend cache placement,
capture schedules, and durable JSON summaries.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from converging_flow.radiant_output import save_radiant_wave_result
from converging_flow.radiant_plotting import (
    save_radiant_wave_animations,
    save_radiant_wave_plots,
)
from converging_flow.radiant_wave import (
    RadiantWaveConfig,
    RadiantWaveResult,
    run_radiant_wave,
)


@dataclass(frozen=True, slots=True)
class ArtifactPlan:
    """Where an example writes artifacts and how it samples animation frames."""

    output_directory: Path
    frames: int = 0
    fps: int = 12

    def __post_init__(self) -> None:
        if self.frames == 1 or self.frames < 0:
            raise ValueError("frames must be zero or at least two")
        ####
        if self.fps < 1:
            raise ValueError("fps must be positive")
        ####
    ####
####


def configure_backend_cache(workspace_root: Path | None = None) -> Path:
    """Set a project-local CuPy cache location and return it.

    CuPy is optional; setting this location is harmless for NumPy-only runs and
    prevents generated kernels from being scattered through user directories.
    """
    root = (workspace_root or Path.cwd()).resolve()
    cache = root / ".tmp" / "cupy-cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CUPY_CACHE_DIR", str(cache))
    return cache
####


def capture_times(final_time: float, frames: int) -> NDArray[np.float64]:
    """Return the inclusive, evenly spaced capture schedule for an example."""
    if final_time <= 0.0:
        raise ValueError("final_time must be positive")
    ####
    if frames < 2:
        raise ValueError("frames must be at least two")
    ####
    return np.linspace(0.0, final_time, frames, dtype=np.float64)
####


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    """Write a stable, human-readable experiment summary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
####


def run_radiant_artifacts(
    config: RadiantWaveConfig,
    artifacts: ArtifactPlan,
    *,
    include_plots: bool = True,
) -> RadiantWaveResult:
    """Run a scalar-wave recipe using the standard result/artifact contract."""
    artifacts.output_directory.mkdir(parents=True, exist_ok=True)
    result = run_radiant_wave(config, snapshot_count=artifacts.frames)
    save_radiant_wave_result(result, artifacts.output_directory)
    if include_plots:
        save_radiant_wave_plots(result, artifacts.output_directory)
        if result.frames:
            save_radiant_wave_animations(result, artifacts.output_directory, fps=artifacts.fps)
        ####
    ####
    return result
####
