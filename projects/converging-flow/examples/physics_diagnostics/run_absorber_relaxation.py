"""Run a generic over-source-to-loss phase followed by absorber insertion."""

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
    ShellRelaxationParameters,
    open_shell_relaxation_config,
    shell_relaxation_parameters_from_json,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Insert a generic right-half absorber during a 3D shell run."
    )
    parser.add_argument("--backend", choices=("auto", "numpy", "cupy"), default="auto")
    parser.add_argument("--resolution", type=int, default=48)
    parser.add_argument("--final-time", type=float, default=0.06)
    parser.add_argument("--insertion-time", type=float, default=0.03)
    parser.add_argument("--frames", type=int, default=121)
    parser.add_argument(
        "--fps",
        type=int,
        default=16,
        help="GIF playback rate; lower values make the experiment longer",
    )
    parser.add_argument(
        "--source-scale",
        type=float,
        default=3.0,
        help="multiply normalized source and feedback rates during the buildup",
    )
    parser.add_argument(
        "--absorber-scale",
        type=float,
        default=12.0,
        help="multiply absorber loss and damping during relaxation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts") / "converging-flow" / "absorber-relaxation",
    )
    parser.add_argument(
        "--parameters",
        type=Path,
        help="JSON recipe file for shell geometry, materials, sources, and event timing",
    )
    arguments = parser.parse_args(argv)
    if arguments.frames < 2:
        raise SystemExit("--frames must be at least two")
    if arguments.fps < 1:
        raise SystemExit("--fps must be positive")
    if arguments.source_scale <= 0.0 or arguments.absorber_scale <= 0.0:
        raise SystemExit("source and absorber scales must be positive")

    configure_backend_cache()
    parameters = (
        shell_relaxation_parameters_from_json(arguments.parameters)
        if arguments.parameters
        else ShellRelaxationParameters(
            resolution=arguments.resolution,
            backend=cast(BackendName, arguments.backend),
            final_time=arguments.final_time,
            insertion_time=arguments.insertion_time,
            source_scale=arguments.source_scale,
            loss_scale=arguments.absorber_scale,
        )
    )
    config = open_shell_relaxation_config(parameters=parameters)
    run_radiant_artifacts(
        config,
        ArtifactPlan(arguments.output, frames=arguments.frames, fps=arguments.fps),
    )
    print(f"Absorber-relaxation artifacts written under {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
