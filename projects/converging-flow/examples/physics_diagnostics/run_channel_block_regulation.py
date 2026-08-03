"""Animate generic loss rods entering a perforated reflective block.

This is a normalized reaction-diffusion and damped scalar-wave visualization.
It uses illustrative dimensionless coefficients and no externally calibrated material model.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from converging_flow.backend import BackendName
from converging_flow.example_runtime import (
    ArtifactPlan,
    configure_backend_cache,
    run_radiant_artifacts,
)
from converging_flow.recipes import (
    PerforatedBlockParameters,
    perforated_block_parameters_from_json,
    perforated_block_regulation_config,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a generic reflective block with 6×4 open channels and "
            "time-ramped loss rods."
        )
    )
    parser.add_argument("--backend", choices=("auto", "numpy", "cupy"), default="auto")
    parser.add_argument("--resolution", type=int, default=56)
    parser.add_argument("--final-time", type=float, default=0.24)
    parser.add_argument("--rod-start", type=float, default=0.05)
    parser.add_argument("--rod-end", type=float, default=0.12)
    parser.add_argument("--rod-fraction", type=float, default=0.50)
    parser.add_argument("--frames", type=int, default=141)
    parser.add_argument("--fps", type=int, default=18)
    parser.add_argument("--source-scale", type=float, default=0.5)
    parser.add_argument("--loss-scale", type=float, default=120.0)
    parser.add_argument(
        "--thermal-exchange",
        type=float,
        default=12.0,
        help="normalized channel-coupled thermal exchange at full insertion",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts") / "converging-flow" / "channel-block-regulation",
    )
    parser.add_argument(
        "--parameters",
        type=Path,
        help="JSON recipe file for geometry, materials, sources, events, and numerics",
    )
    arguments = parser.parse_args(argv)
    if arguments.resolution < 24:
        raise SystemExit("--resolution must be at least 24 for the 6×4 channel grid")
    if arguments.frames < 2 or arguments.fps < 1:
        raise SystemExit("--frames must be at least two and --fps must be positive")
    if (
        arguments.source_scale <= 0.0
        or arguments.loss_scale <= 0.0
        or arguments.thermal_exchange < 0.0
    ):
        raise SystemExit(
            "source/loss scales must be positive and exchange non-negative"
        )
    if not 0.0 <= arguments.rod_fraction <= 1.0:
        raise SystemExit("--rod-fraction must lie between zero and one")

    configure_backend_cache()
    parameters = (
        perforated_block_parameters_from_json(arguments.parameters)
        if arguments.parameters
        else PerforatedBlockParameters(
            resolution=arguments.resolution,
            backend=cast(BackendName, arguments.backend),
            final_time=arguments.final_time,
            insertion_start_time=arguments.rod_start,
            insertion_end_time=arguments.rod_end,
            insertion_fraction=arguments.rod_fraction,
            source_scale=arguments.source_scale,
            loss_scale=arguments.loss_scale,
            thermal_exchange=arguments.thermal_exchange,
        )
    )
    config = perforated_block_regulation_config(parameters=parameters)
    run_radiant_artifacts(
        config,
        ArtifactPlan(arguments.output, frames=arguments.frames, fps=arguments.fps),
    )
    print(f"Channel-block artifacts written under {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
