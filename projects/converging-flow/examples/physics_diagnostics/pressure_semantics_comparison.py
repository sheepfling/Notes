from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def build_comparison(
    radiant_state_path: Path,
    reactive_state_path: Path,
    output_path: Path,
) -> None:
    with np.load(radiant_state_path) as radiant_payload:
        radiant_x = np.asarray(
            radiant_payload["coordinate_0"],
            dtype=np.float64,
        )
        wave_pressure = np.asarray(
            radiant_payload["wave_pressure"],
            dtype=np.float64,
        )
    ####
    with np.load(reactive_state_path) as reactive_payload:
        reactive_x = np.asarray(
            reactive_payload["coordinate"],
            dtype=np.float64,
        )
        thermodynamic_pressure = np.asarray(
            reactive_payload["pressure"],
            dtype=np.float64,
        )
        velocity = np.asarray(
            reactive_payload["velocity"],
            dtype=np.float64,
        )
    ####

    wave_force = -np.gradient(
        wave_pressure,
        float(radiant_x[1] - radiant_x[0]),
        edge_order=1,
    )
    pressure_perturbation = thermodynamic_pressure - 1.0

    figure, axes_grid = plt.subplots(2, 2, figsize=(14, 8), sharex="col")
    axes_grid[0, 0].plot(radiant_x, wave_pressure)
    axes_grid[0, 0].set_ylabel("wave-pressure proxy")
    axes_grid[0, 0].set_title("Scalar-wave diagnostic")
    axes_grid[1, 0].plot(radiant_x, wave_force)
    axes_grid[1, 0].axhline(0.0, linewidth=0.8)
    axes_grid[1, 0].set_ylabel("−∂p_proxy/∂x")
    axes_grid[1, 0].set_xlabel("position")
    axes_grid[1, 0].set_title("Derived diagnostic force direction")

    axes_grid[0, 1].plot(reactive_x, pressure_perturbation)
    axes_grid[0, 1].set_ylabel("thermodynamic Δpressure")
    axes_grid[0, 1].set_title("Euler EOS pressure")
    axes_grid[1, 1].plot(reactive_x, velocity)
    axes_grid[1, 1].axhline(0.0, linewidth=0.8)
    axes_grid[1, 1].set_ylabel("fluid velocity")
    axes_grid[1, 1].set_xlabel("position")
    axes_grid[1, 1].set_title("Material motion produced by Euler fluxes")

    for axes in axes_grid.flat:
        axes.grid(True, alpha=0.25)
    ####
    figure.suptitle(
        "Two pressure concepts: wave-energy diagnostic versus "
        "thermodynamic pressure that accelerates material"
    )
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)
####


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--radiant-state",
        type=Path,
        default=Path("examples/physics_diagnostics/radiant_1d/radiant_wave_state.npz"),
    )
    parser.add_argument(
        "--reactive-state",
        type=Path,
        default=Path(
            "examples/physics_diagnostics/reactive_pressure/reactive_pressure_state.npz"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "examples/physics_diagnostics/pressure_semantics_comparison.png"
        ),
    )
    arguments = parser.parse_args()
    build_comparison(
        arguments.radiant_state,
        arguments.reactive_state,
        arguments.output,
    )
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
