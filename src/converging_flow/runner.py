"""Portable orchestration for the standard Converging Flow artifact suite."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence

from converging_flow.cli import main as cli_main


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="converging-flow-run",
        description="Generate the standard Euler, reaction, and radiant-wave artifacts.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "cupy"),
        default="auto",
        help="array backend for Euler and radiant-wave experiments",
    )
    parser.add_argument(
        "--reaction-backend",
        choices=("numpy", "numba"),
        default="numpy",
        help="reaction-diffusion backend",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts") / "converging-flow" / "scripted-run",
    )
    parser.add_argument(
        "--full-resolution",
        action="store_true",
        help="use the documented 1D/2D/3D suite resolutions",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="write numerical outputs without images or animations",
    )
    return parser


def _run_step(arguments: list[str]) -> None:
    print("Running: python -m converging_flow " + " ".join(arguments), flush=True)
    result = cli_main(arguments)
    if result:
        raise SystemExit(result)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    if "CUPY_CACHE_DIR" not in os.environ:
        cache = Path(".tmp") / "cupy-cache"
        cache.mkdir(parents=True, exist_ok=True)
        os.environ["CUPY_CACHE_DIR"] = str(cache.resolve())

    if arguments.full_resolution:
        n1, n2, n3, final_time = 512, 128, 40, 0.18
    else:
        n1, n2, n3, final_time = 64, 24, 12, 0.02

    output_root = arguments.output_root
    common = [] if not arguments.no_plots else ["--no-plots"]
    _run_step(
        [
            "suite",
            "--n1",
            str(n1),
            "--n2",
            str(n2),
            "--n3",
            str(n3),
            "--final-time",
            str(final_time),
            "--backend",
            arguments.backend,
            "--output",
            str(output_root / "euler"),
            *common,
        ]
    )
    _run_step(
        [
            "reaction-suite",
            "--n1",
            str(n1),
            "--n2",
            str(n2),
            "--n3",
            str(n3),
            "--final-time",
            str(final_time),
            "--backend",
            arguments.reaction_backend,
            "--output",
            str(output_root / "reaction"),
            *common,
        ]
    )
    _run_step(
        [
            "radiant-wave-run",
            "--dim",
            "2",
            "--n",
            str(n2),
            "--final-time",
            str(final_time),
            "--backend",
            arguments.backend,
            "--output",
            str(output_root / "radiant-wave"),
            *common,
        ]
    )
    print(f"Artifacts written under {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
