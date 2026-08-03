from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from converging_flow.config import Dimension, SimulationConfig
from converging_flow.example_runtime import ArtifactPlan, run_radiant_artifacts
from converging_flow.experiment import SimulationResult, run_simulation
from converging_flow.output import save_result
from converging_flow.plotting import save_animations, save_comparison, save_plots
from converging_flow.radiant_wave import (
    RadiantWaveConfig,
    RadiantWaveResult,
    radiant_wave_config,
)
from converging_flow.reaction_diffusion import (
    ReactionBackend,
    ReactionDiffusionConfig,
    ReactionResult,
    reaction_config,
    run_reaction_diffusion,
)
from converging_flow.reaction_output import save_reaction_result
from converging_flow.reaction_plotting import (
    save_reaction_animations,
    save_reaction_comparison,
    save_reaction_plots,
)


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 8:
        raise argparse.ArgumentTypeError("resolution must be at least 8")
    ####
    return parsed
####


def _frame_count(value: str) -> int:
    parsed = int(value)
    if parsed == 1 or parsed < 0:
        raise argparse.ArgumentTypeError("frames must be zero or at least two")
    ####
    return parsed
####


def _positive_fps(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("fps must be positive")
    ####
    return parsed
####


def _add_visualization_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--frames",
        type=_frame_count,
        default=0,
        help="capture this many equally spaced frames and write GIF animations",
    )
    parser.add_argument(
        "--fps",
        type=_positive_fps,
        default=12,
        help="animation playback rate",
    )
    parser.add_argument("--no-plots", action="store_true")
####


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="converging-flow",
        description=(
            "Vectorized inert-flow and generic reaction-diffusion experiments "
            "in 1D, 2D, and 3D."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run one dimensionality")
    run_parser.add_argument("--dim", type=int, choices=(1, 2, 3), required=True)
    run_parser.add_argument("--n", type=_positive_integer, required=True)
    run_parser.add_argument("--final-time", type=float, default=0.18)
    run_parser.add_argument("--mach", type=float, default=0.75)
    run_parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "cupy"),
        default="auto",
        help="array backend; auto prefers a usable CUDA device",
    )
    run_parser.add_argument("--output", type=Path, default=Path("outputs/run"))
    _add_visualization_arguments(run_parser)

    suite_parser = subparsers.add_parser("suite", help="run 1D, 2D, and 3D")
    suite_parser.add_argument("--n1", type=_positive_integer, default=512)
    suite_parser.add_argument("--n2", type=_positive_integer, default=128)
    suite_parser.add_argument("--n3", type=_positive_integer, default=40)
    suite_parser.add_argument("--final-time", type=float, default=0.18)
    suite_parser.add_argument("--mach", type=float, default=0.75)
    suite_parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "cupy"),
        default="auto",
        help="array backend; auto prefers a usable CUDA device",
    )
    suite_parser.add_argument("--output", type=Path, default=Path("outputs/suite"))
    _add_visualization_arguments(suite_parser)

    reaction_run_parser = subparsers.add_parser(
        "reaction-run",
        help="run one generic reaction-diffusion-wave dimensionality",
    )
    reaction_run_parser.add_argument(
        "--dim", type=int, choices=(1, 2, 3), required=True
    )
    reaction_run_parser.add_argument("--n", type=_positive_integer, required=True)
    reaction_run_parser.add_argument("--final-time", type=float, default=1.0)
    reaction_run_parser.add_argument(
        "--backend",
        choices=("numpy", "numba"),
        default="numpy",
        help="numerical backend; numba has one-time compilation cost",
    )
    reaction_run_parser.add_argument(
        "--output", type=Path, default=Path("outputs/reaction-run")
    )
    _add_visualization_arguments(reaction_run_parser)

    reaction_suite_parser = subparsers.add_parser(
        "reaction-suite",
        help="run generic reaction-diffusion-wave demos in 1D, 2D, and 3D",
    )
    reaction_suite_parser.add_argument("--n1", type=_positive_integer, default=512)
    reaction_suite_parser.add_argument("--n2", type=_positive_integer, default=128)
    reaction_suite_parser.add_argument("--n3", type=_positive_integer, default=40)
    reaction_suite_parser.add_argument("--final-time", type=float, default=1.0)
    reaction_suite_parser.add_argument(
        "--backend",
        choices=("numpy", "numba"),
        default="numpy",
        help="numerical backend; numba has one-time compilation cost per dimension",
    )
    reaction_suite_parser.add_argument(
        "--output", type=Path, default=Path("outputs/reaction-suite")
    )
    _add_visualization_arguments(reaction_suite_parser)

    radiant_parser = subparsers.add_parser(
        "radiant-wave-run",
        help=(
            "run one heterogeneous autocatalytic reaction-diffusion and "
            "damped scalar-wave experiment"
        ),
    )
    radiant_parser.add_argument(
        "--dim", type=int, choices=(1, 2, 3), required=True
    )
    radiant_parser.add_argument("--n", type=_positive_integer, required=True)
    radiant_parser.add_argument("--final-time", type=float, default=1.0)
    radiant_parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "cupy"),
        default="auto",
        help="array backend; auto prefers a usable CUDA device",
    )
    radiant_parser.add_argument(
        "--diffusion",
        choices=("auto", "explicit", "crank-nicolson"),
        default="auto",
        help="activity/heat diffusion integrator",
    )
    radiant_parser.add_argument(
        "--output", type=Path, default=Path("outputs/radiant-wave-run")
    )
    _add_visualization_arguments(radiant_parser)
    return parser
####


def _config(
    dimensions: int,
    resolution: int,
    final_time: float,
    mach: float,
    backend: str = "numpy",
) -> SimulationConfig:
    dimension = cast(Dimension, dimensions)
    return SimulationConfig(
        dimensions=dimension,
        resolution=(resolution,) * dimensions,
        final_time=final_time,
        inward_mach=mach,
        backend=backend,  # type: ignore[arg-type]
    )
####


def _run_one(
    config: SimulationConfig,
    output: Path,
    make_plots: bool,
    snapshot_count: int,
    fps: int,
) -> SimulationResult:
    print(
        f"running {config.dimensions}D {config.resolution} "
        f"to t={config.final_time:.4f}"
    )
    result = run_simulation(config, snapshot_count=snapshot_count)
    save_result(result, output)
    if make_plots:
        save_plots(result, output)
        if result.frames:
            save_animations(result, output, fps=fps)
        ####
    ####
    mass_change = (
        result.final_diagnostics.mass / result.initial_diagnostics.mass - 1.0
    )
    energy_change = (
        result.final_diagnostics.total_energy
        / result.initial_diagnostics.total_energy
        - 1.0
    )
    print(
        f"completed in {result.steps} steps on {result.resolved_backend}; "
        f"mass change={mass_change:+.3e}; "
        f"energy change={energy_change:+.3e}; "
        f"frames={len(result.frames)}"
    )
    return result
####


def _run_reaction_one(
    config: ReactionDiffusionConfig,
    output: Path,
    make_plots: bool,
    snapshot_count: int,
    fps: int,
) -> ReactionResult:
    print(
        f"running generic reaction-diffusion-wave {config.dimensions}D "
        f"{config.resolution} to t={config.final_time:.4f} "
        f"with {config.backend}"
    )
    result = run_reaction_diffusion(config, snapshot_count=snapshot_count)
    save_reaction_result(result, output)
    if make_plots:
        save_reaction_plots(result, output)
        if result.frames:
            save_reaction_animations(result, output, fps=fps)
        ####
    ####
    print(
        f"completed in {result.steps} steps; "
        f"max activity={result.final_diagnostics.maximum_activity:.3f}; "
        f"max heat={result.final_diagnostics.maximum_heat:.3f}; "
        f"frames={len(result.frames)}"
    )
    return result
####


def _run_radiant_wave_one(
    config: RadiantWaveConfig,
    output: Path,
    make_plots: bool,
    snapshot_count: int,
    fps: int,
) -> RadiantWaveResult:
    print(
        f"running radiant-wave autocatalytic {config.dimensions}D "
        f"{config.resolution} to t={config.final_time:.4f}; "
        f"backend={config.backend}; diffusion={config.diffusion_method}"
    )
    result = run_radiant_artifacts(
        config,
        ArtifactPlan(output, frames=snapshot_count, fps=fps),
        include_plots=make_plots,
    )
    print(
        f"completed in {result.steps} steps on {result.resolved_backend}; "
        f"diffusion={result.resolved_diffusion_method}; "
        f"max activity={result.final_diagnostics.maximum_activity:.3f}; "
        f"wave energy={result.final_diagnostics.total_wave_energy:.3e}; "
        f"frames={len(result.frames)}"
    )
    return result
####


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)

    if arguments.command == "run":
        config = _config(
            arguments.dim,
            arguments.n,
            arguments.final_time,
            arguments.mach,
            arguments.backend,
        )
        _run_one(
            config,
            arguments.output,
            not arguments.no_plots,
            arguments.frames,
            arguments.fps,
        )
        return 0
    ####

    if arguments.command == "reaction-run":
        config = reaction_config(
            arguments.dim,
            arguments.n,
            arguments.final_time,
            cast(ReactionBackend, arguments.backend),
        )
        _run_reaction_one(
            config,
            arguments.output,
            not arguments.no_plots,
            arguments.frames,
            arguments.fps,
        )
        return 0
    ####

    if arguments.command == "radiant-wave-run":
        config = radiant_wave_config(
            arguments.dim,
            arguments.n,
            arguments.final_time,
            arguments.backend,
            arguments.diffusion,
        )
        _run_radiant_wave_one(
            config,
            arguments.output,
            not arguments.no_plots,
            arguments.frames,
            arguments.fps,
        )
        return 0
    ####

    if arguments.command == "reaction-suite":
        resolutions = {1: arguments.n1, 2: arguments.n2, 3: arguments.n3}
        reaction_results: list[ReactionResult] = []
        for dimensions in (1, 2, 3):
            output = arguments.output / f"{dimensions}d"
            config = reaction_config(
                dimensions,
                resolutions[dimensions],
                arguments.final_time,
                cast(ReactionBackend, arguments.backend),
            )
            reaction_results.append(
                _run_reaction_one(
                    config,
                    output,
                    not arguments.no_plots,
                    arguments.frames,
                    arguments.fps,
                )
            )
        ####
        if not arguments.no_plots:
            save_reaction_comparison(reaction_results, arguments.output)
        ####
        return 0
    ####

    resolutions = {1: arguments.n1, 2: arguments.n2, 3: arguments.n3}
    results: list[SimulationResult] = []
    for dimensions in (1, 2, 3):
        output = arguments.output / f"{dimensions}d"
        config = _config(
            dimensions,
            resolutions[dimensions],
            arguments.final_time,
            arguments.mach,
            arguments.backend,
        )
        results.append(
            _run_one(
                config,
                output,
                not arguments.no_plots,
                arguments.frames,
                arguments.fps,
            )
        )
    ####
    if not arguments.no_plots:
        save_comparison(results, arguments.output)
    ####
    return 0
####
