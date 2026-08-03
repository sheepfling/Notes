"""Run a generic over-source-to-loss phase followed by absorber insertion."""

from __future__ import annotations

import argparse
import os
from dataclasses import replace
from pathlib import Path
from typing import Sequence, cast

from converging_flow.backend import BackendName
from converging_flow.radiant_output import save_radiant_wave_result
from converging_flow.radiant_plotting import (
    save_radiant_wave_animations,
    save_radiant_wave_plots,
)
from converging_flow.radiant_wave import RadiantWaveConfig, run_radiant_wave


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Insert a generic right-half absorber during a 3D shell run."
    )
    parser.add_argument("--backend", choices=("auto", "numpy", "cupy"), default="auto")
    parser.add_argument("--resolution", type=int, default=24)
    parser.add_argument("--final-time", type=float, default=0.02)
    parser.add_argument("--insertion-time", type=float, default=0.01)
    parser.add_argument("--frames", type=int, default=61)
    parser.add_argument(
        "--source-scale",
        type=float,
        default=3.0,
        help="multiply normalized source and feedback rates during the buildup",
    )
    parser.add_argument(
        "--absorber-scale",
        type=float,
        default=4.0,
        help="multiply absorber loss and damping during relaxation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts") / "converging-flow" / "absorber-relaxation",
    )
    arguments = parser.parse_args(argv)
    if arguments.frames < 2:
        raise SystemExit("--frames must be at least two")
    if arguments.source_scale <= 0.0 or arguments.absorber_scale <= 0.0:
        raise SystemExit("source and absorber scales must be positive")

    cache = Path(".tmp") / "cupy-cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CUPY_CACHE_DIR", str(cache.resolve()))
    absorber = replace(
        RadiantWaveConfig(
            dimensions=3,
            resolution=(arguments.resolution,) * 3,
        ).absorber,
        loss_rate=2.80 * arguments.absorber_scale,
        heat_loss_rate=2.20 * arguments.absorber_scale,
        wave_damping=4.50 * arguments.absorber_scale,
    )
    config = RadiantWaveConfig(
        dimensions=3,
        resolution=(arguments.resolution,) * 3,
        final_time=arguments.final_time,
        backend=cast(BackendName, arguments.backend),
        material_layout="spherical-shell-open",
        absorber_insertion_time=arguments.insertion_time,
        heat_source_rate=1.50 * arguments.source_scale,
        heat_feedback=0.25 * arguments.source_scale,
        wave_source_rate=0.90 * arguments.source_scale,
        wave_pressure_feedback=0.08 * arguments.source_scale,
        absorber=absorber,
    )
    result = run_radiant_wave(config, snapshot_count=arguments.frames)
    save_radiant_wave_result(result, arguments.output)
    save_radiant_wave_plots(result, arguments.output)
    save_radiant_wave_animations(result, arguments.output, fps=12)
    print(f"Absorber-relaxation artifacts written under {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
