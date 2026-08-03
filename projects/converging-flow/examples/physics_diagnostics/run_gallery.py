"""Generate the complete radiant/pressure physics visualization gallery."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from converging_flow.cli import main as cli_main
from converging_flow.radiant_output import save_radiant_wave_result
from converging_flow.radiant_plotting import (
    save_radiant_wave_animations,
    save_radiant_wave_plots,
)
from converging_flow.radiant_wave import RadiantWaveConfig, run_radiant_wave


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError("could not locate the repository pyproject.toml")


def _run_script(script: Path, arguments: list[str], env: dict[str, str]) -> None:
    command = [sys.executable, str(script), *arguments]
    print("Running: " + " ".join(command), flush=True)
    subprocess.run(command, check=True, env=env)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="converging-flow-gallery",
        description="Generate the CPU/GPU physics diagnostics visualization gallery.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "cupy"),
        default="auto",
        help="array backend for radiant and reactive simulations",
    )
    parser.add_argument("--one-d-resolution", type=int, default=64)
    parser.add_argument("--three-d-resolution", type=int, default=24)
    parser.add_argument("--resolution", type=int, default=64)
    parser.add_argument("--final-time", type=float, default=0.02)
    parser.add_argument("--frames", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts") / "converging-flow" / "physics-gallery",
    )
    return parser


def _run_spherical_shell(
    backend: str,
    resolution: int,
    final_time: float,
    frames: int,
    output: Path,
) -> None:
    config = RadiantWaveConfig(
        dimensions=3,
        resolution=(resolution,) * 3,
        final_time=final_time,
        backend=backend,  # type: ignore[arg-type]
        material_layout="spherical-shell",
    )
    print(
        f"running asymmetric spherical-shell 3D {config.resolution} "
        f"to t={config.final_time:.4f}; backend={backend}",
        flush=True,
    )
    result = run_radiant_wave(config, snapshot_count=frames)
    save_radiant_wave_result(result, output)
    save_radiant_wave_plots(result, output)
    if result.frames:
        save_radiant_wave_animations(result, output, fps=12)
    print(
        f"completed in {result.steps} steps on {result.resolved_backend}; "
        f"frames={len(result.frames)}",
        flush=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    if arguments.frames < 2:
        raise SystemExit("--frames must be at least two")

    repository_root = _repository_root()
    output_root = arguments.output
    output_root.mkdir(parents=True, exist_ok=True)
    cache = repository_root / ".tmp" / "cupy-cache"
    cache.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.setdefault("CUPY_CACHE_DIR", str(cache.resolve()))

    cli_main(
        [
            "radiant-wave-run",
            "--dim",
            "1",
            "--n",
            str(arguments.one_d_resolution),
            "--final-time",
            str(arguments.final_time),
            "--backend",
            arguments.backend,
            "--frames",
            str(arguments.frames),
            "--output",
            str(output_root / "radiant_1d"),
        ]
    )
    _run_spherical_shell(
        arguments.backend,
        arguments.three_d_resolution,
        arguments.final_time,
        arguments.frames,
        output_root / "spherical_shell_3d",
    )

    reactive_script = (
        Path(__file__).resolve().parents[1]
        / "backend_agnostic"
        / "reactive_pressure_demo.py"
    )
    reactive_output = output_root / "reactive_pressure"
    _run_script(
        reactive_script,
        [
            "--backend",
            arguments.backend,
            "--resolution",
            str(arguments.resolution),
            "--final-time",
            str(arguments.final_time),
            "--frames",
            str(arguments.frames),
            "--output",
            str(reactive_output),
        ],
        environment,
    )

    comparison_script = (
        Path(__file__).resolve().parent / "pressure_semantics_comparison.py"
    )
    _run_script(
        comparison_script,
        [
            "--radiant-state",
            str(output_root / "radiant_1d" / "radiant_wave_state.npz"),
            "--reactive-state",
            str(reactive_output / "reactive_pressure_state.npz"),
            "--output",
            str(output_root / "pressure_semantics_comparison.png"),
        ],
        environment,
    )
    print(f"Physics visualization gallery written under {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
