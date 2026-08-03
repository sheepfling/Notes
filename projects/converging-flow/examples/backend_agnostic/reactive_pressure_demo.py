from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from numpy.typing import NDArray

from converging_flow.backend import (
    Array,
    ArrayBackend,
    BackendName,
    get_array_backend,
)
from converging_flow.reactive_euler import (
    ReactiveEulerConfig,
    advance_reactive_euler_split,
    primitive_to_reactive_conservative,
    reactive_conservative_to_primitive,
    stable_reactive_timestep,
)

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class ReactiveFrame:
    time: float
    density: FloatArray
    velocity: FloatArray
    pressure: FloatArray
    progress: FloatArray
    progress_rate: FloatArray
####


def _capture_frame(
    time: float,
    state: Array,
    source_profile: Array,
    config: ReactiveEulerConfig,
    backend: ArrayBackend,
) -> ReactiveFrame:
    density, velocity, pressure, progress = reactive_conservative_to_primitive(
        state,
        config,
        backend,
    )
    progress_rate = 8.0 * source_profile * (1.0 - progress)
    return ReactiveFrame(
        time=time,
        density=backend.to_numpy(density),
        velocity=backend.to_numpy(velocity[0]),
        pressure=backend.to_numpy(pressure),
        progress=backend.to_numpy(progress),
        progress_rate=backend.to_numpy(progress_rate),
    )
####


def _save_final_coupling_panel(
    coordinate: FloatArray,
    frame: ReactiveFrame,
    config: ReactiveEulerConfig,
    output_directory: Path,
) -> None:
    temperature_proxy = frame.pressure / frame.density
    internal_energy = frame.pressure / (config.gamma - 1.0)
    kinetic_energy = 0.5 * frame.density * frame.velocity * frame.velocity

    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    fields = (
        (frame.progress, "reaction progress"),
        (frame.pressure, "thermodynamic pressure"),
        (frame.velocity, "fluid velocity"),
        (frame.density, "density"),
        (temperature_proxy, "temperature proxy p/ρ"),
        (internal_energy + kinetic_energy, "total energy density"),
    )
    for axes, (values, label) in zip(
        axes_grid.flat,
        fields,
        strict=True,
    ):
        axes.plot(coordinate, values)
        axes.set_title(label)
        axes.set_ylabel(label)
        axes.grid(True, alpha=0.25)
    ####
    for axes in axes_grid[-1, :]:
        axes.set_xlabel("position")
    ####
    figure.suptitle(
        "Reactive-Euler coupling: progress → heat release → pressure → motion"
    )
    figure.tight_layout()
    figure.savefig(
        output_directory / "reactive_coupling_chain.png",
        dpi=180,
    )
    plt.close(figure)
####


def _save_space_time(
    coordinate: FloatArray,
    frames: tuple[ReactiveFrame, ...],
    output_directory: Path,
) -> None:
    times = np.array([frame.time for frame in frames])
    progress = np.stack([frame.progress for frame in frames])
    pressure_perturbation = np.stack(
        [frame.pressure - 1.0 for frame in frames]
    )
    velocity = np.stack([frame.velocity for frame in frames])
    extent = (
        float(coordinate[0]),
        float(coordinate[-1]),
        float(times[0]),
        float(times[-1]),
    )
    velocity_bound = max(
        abs(float(np.min(velocity))),
        abs(float(np.max(velocity))),
    )

    figure, axes_grid = plt.subplots(3, 1, figsize=(11, 11), sharex=True)
    images = (
        axes_grid[0].imshow(
            progress,
            origin="lower",
            extent=extent,
            aspect="auto",
            vmin=0.0,
            vmax=1.0,
        ),
        axes_grid[1].imshow(
            pressure_perturbation,
            origin="lower",
            extent=extent,
            aspect="auto",
        ),
        axes_grid[2].imshow(
            velocity,
            origin="lower",
            extent=extent,
            aspect="auto",
            vmin=-velocity_bound,
            vmax=velocity_bound,
        ),
    )
    labels = (
        "reaction progress",
        "pressure perturbation",
        "velocity",
    )
    for axes, image, label in zip(
        axes_grid,
        images,
        labels,
        strict=True,
    ):
        axes.set_ylabel("time")
        axes.set_title(label)
        figure.colorbar(image, ax=axes, label=label)
    ####
    axes_grid[-1].set_xlabel("position")
    figure.suptitle("Reactive pressure and acceleration through space and time")
    figure.tight_layout()
    figure.savefig(
        output_directory / "reactive_pressure_space_time.png",
        dpi=180,
    )
    plt.close(figure)
####


def _save_pressure_acceleration(
    coordinate: FloatArray,
    frame: ReactiveFrame,
    output_directory: Path,
) -> None:
    spacing = float(coordinate[1] - coordinate[0])
    pressure_gradient = np.gradient(frame.pressure, spacing, edge_order=1)
    pressure_acceleration = -pressure_gradient / frame.density

    figure, axes_grid = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    axes_grid[0].plot(coordinate, frame.pressure - 1.0)
    axes_grid[0].set_ylabel("Δpressure")
    axes_grid[0].set_title("Pressure perturbation created by heat release")
    axes_grid[1].plot(coordinate, pressure_acceleration)
    axes_grid[1].axhline(0.0, linewidth=0.8)
    axes_grid[1].set_ylabel("−∂p/∂x / ρ")
    axes_grid[1].set_title("Instantaneous pressure-gradient acceleration")
    axes_grid[2].plot(coordinate, frame.velocity)
    axes_grid[2].axhline(0.0, linewidth=0.8)
    axes_grid[2].set_ylabel("velocity")
    axes_grid[2].set_xlabel("position")
    axes_grid[2].set_title("Resulting outward fluid motion")
    for axes in axes_grid:
        axes.grid(True, alpha=0.25)
    ####
    figure.suptitle(
        "Actual pressure coupling: EOS pressure gradient accelerates material"
    )
    figure.tight_layout()
    figure.savefig(
        output_directory / "reactive_pressure_acceleration.png",
        dpi=180,
    )
    plt.close(figure)
####


def _save_energy_budget(
    coordinate: FloatArray,
    frames: tuple[ReactiveFrame, ...],
    config: ReactiveEulerConfig,
    output_directory: Path,
) -> None:
    spacing = float(coordinate[1] - coordinate[0])
    times = np.array([frame.time for frame in frames])
    internal = np.array(
        [
            np.sum(frame.pressure / (config.gamma - 1.0)) * spacing
            for frame in frames
        ]
    )
    kinetic = np.array(
        [
            np.sum(
                0.5
                * frame.density
                * frame.velocity
                * frame.velocity
            )
            * spacing
            for frame in frames
        ]
    )
    total = internal + kinetic
    released = np.array(
        [
            config.heat_release_per_mass
            * np.sum(frame.density * frame.progress)
            * spacing
            for frame in frames
        ]
    )
    reacted_mass = np.array(
        [
            np.sum(frame.density * frame.progress) * spacing
            for frame in frames
        ]
    )

    energy_residual = total - total[0] - released
    figure, axes_grid = plt.subplots(2, 2, figsize=(14, 9), sharex=True)
    axes_grid[0, 0].plot(
        times,
        total - total[0],
        label="total increase",
    )
    axes_grid[0, 0].plot(
        times,
        released,
        linestyle="--",
        label="released heat",
    )
    axes_grid[0, 0].set_ylabel("integrated energy")
    axes_grid[0, 0].set_title("Energy input versus conserved total")
    axes_grid[0, 0].legend()

    axes_grid[0, 1].plot(times, kinetic)
    axes_grid[0, 1].set_ylabel("kinetic energy")
    axes_grid[0, 1].set_title("Pressure work converted into motion")

    axes_grid[1, 0].plot(times, energy_residual)
    axes_grid[1, 0].axhline(0.0, linewidth=0.8)
    axes_grid[1, 0].set_ylabel("energy residual")
    axes_grid[1, 0].set_xlabel("time")
    axes_grid[1, 0].set_title("Total increase − released heat")

    axes_grid[1, 1].plot(times, reacted_mass)
    axes_grid[1, 1].set_ylabel("reacted mass proxy")
    axes_grid[1, 1].set_xlabel("time")
    axes_grid[1, 1].set_title("Integrated reaction progress")
    for axes in axes_grid.flat:
        axes.grid(True, alpha=0.25)
    ####
    figure.suptitle("Reactive-Euler integral budgets")
    figure.tight_layout()
    figure.savefig(
        output_directory / "reactive_energy_budget.png",
        dpi=180,
    )
    plt.close(figure)
####


def _save_animation(
    coordinate: FloatArray,
    frames: tuple[ReactiveFrame, ...],
    output_directory: Path,
    fps: int,
) -> None:
    progress_max = 1.0
    pressure_min = min(float(np.min(frame.pressure)) for frame in frames)
    pressure_max = max(float(np.max(frame.pressure)) for frame in frames)
    velocity_bound = max(
        max(abs(float(np.min(frame.velocity))), abs(float(np.max(frame.velocity))))
        for frame in frames
    )

    figure, axes_grid = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    progress_line, = axes_grid[0].plot(coordinate, frames[0].progress)
    pressure_line, = axes_grid[1].plot(coordinate, frames[0].pressure)
    velocity_line, = axes_grid[2].plot(coordinate, frames[0].velocity)
    axes_grid[0].set_ylim(0.0, progress_max)
    axes_grid[1].set_ylim(pressure_min, pressure_max)
    axes_grid[2].set_ylim(-velocity_bound, velocity_bound)
    axes_grid[0].set_ylabel("progress")
    axes_grid[1].set_ylabel("pressure")
    axes_grid[2].set_ylabel("velocity")
    axes_grid[2].set_xlabel("position")
    for axes in axes_grid:
        axes.grid(True, alpha=0.25)
    ####

    def update(index: int) -> tuple[object, ...]:
        frame = frames[index]
        progress_line.set_ydata(frame.progress)
        pressure_line.set_ydata(frame.pressure)
        velocity_line.set_ydata(frame.velocity)
        figure.suptitle(
            "Reactive-Euler pressure-driven motion "
            f"| t = {frame.time:.4f}"
        )
        return progress_line, pressure_line, velocity_line
    ####

    animation = FuncAnimation(
        figure,
        update,
        frames=len(frames),
        interval=1000 / fps,
        blit=False,
    )
    figure.tight_layout()
    animation.save(
        output_directory / "reactive_pressure_evolution.gif",
        writer=PillowWriter(fps=fps),
        dpi=120,
    )
    plt.close(figure)
####


def run_demo(
    output_directory: Path,
    requested_backend: BackendName,
    resolution: int = 512,
    final_time: float = 0.08,
    snapshot_count: int = 33,
    fps: int = 12,
) -> None:
    if snapshot_count < 2:
        raise ValueError("snapshot_count must be at least two")
    ####
    backend = get_array_backend(requested_backend)
    config = ReactiveEulerConfig(
        gamma=1.4,
        heat_release_per_mass=0.75,
    )
    half_extent = 1.0
    spacing = (2.0 * half_extent / resolution,)
    coordinate_numpy = np.linspace(
        -half_extent + 0.5 * spacing[0],
        half_extent - 0.5 * spacing[0],
        resolution,
        dtype=np.float64,
    )
    coordinate = backend.asarray(coordinate_numpy)
    density = backend.xp.ones(resolution, dtype=np.float64)
    velocity = backend.xp.zeros((1, resolution), dtype=np.float64)
    pressure = backend.xp.ones(resolution, dtype=np.float64)
    progress = backend.xp.zeros(resolution, dtype=np.float64)
    state = primitive_to_reactive_conservative(
        density,
        velocity,
        pressure,
        progress,
        config,
        backend,
    )

    source_width = 0.10
    source_profile = backend.xp.exp(
        -0.5 * (coordinate / source_width) ** 2
    )
    target_times = np.linspace(0.0, final_time, snapshot_count)
    frames: list[ReactiveFrame] = [
        _capture_frame(
            0.0,
            state,
            source_profile,
            config,
            backend,
        )
    ]
    next_target = 1
    time = 0.0
    steps = 0
    while time < final_time:
        _density, _velocity, _pressure, progress = (
            reactive_conservative_to_primitive(state, config, backend)
        )
        progress_rate = 8.0 * source_profile * (1.0 - progress)
        timestep = min(
            stable_reactive_timestep(
                state,
                spacing,
                cfl=0.30,
                config=config,
                backend=backend,
            ),
            5.0e-4,
            final_time - time,
        )
        state = advance_reactive_euler_split(
            state,
            progress_rate,
            force_density=None,
            timestep=timestep,
            spacing=spacing,
            config=config,
            backend=backend,
        )
        time += timestep
        steps += 1

        while (
            next_target < snapshot_count
            and time >= target_times[next_target] - 1.0e-14
        ):
            frames.append(
                _capture_frame(
                    time,
                    state,
                    source_profile,
                    config,
                    backend,
                )
            )
            next_target += 1
        ####
    ####

    backend.synchronize()
    final_frame = frames[-1]
    frame_tuple = tuple(frames)

    output_directory.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_directory / "reactive_pressure_state.npz",
        coordinate=coordinate_numpy,
        density=final_frame.density,
        velocity=final_frame.velocity,
        pressure=final_frame.pressure,
        progress=final_frame.progress,
        time=np.array(time),
        steps=np.array(steps),
        frame_time=np.array([frame.time for frame in frame_tuple]),
        frame_density=np.stack([frame.density for frame in frame_tuple]),
        frame_velocity=np.stack([frame.velocity for frame in frame_tuple]),
        frame_pressure=np.stack([frame.pressure for frame in frame_tuple]),
        frame_progress=np.stack([frame.progress for frame in frame_tuple]),
        frame_progress_rate=np.stack(
            [frame.progress_rate for frame in frame_tuple]
        ),
    )

    _save_final_coupling_panel(
        coordinate_numpy,
        final_frame,
        config,
        output_directory,
    )
    _save_space_time(coordinate_numpy, frame_tuple, output_directory)
    _save_pressure_acceleration(
        coordinate_numpy,
        frame_tuple[len(frame_tuple) // 2],
        output_directory,
    )
    _save_energy_budget(
        coordinate_numpy,
        frame_tuple,
        config,
        output_directory,
    )
    _save_animation(
        coordinate_numpy,
        frame_tuple,
        output_directory,
        fps,
    )

    summary = {
        "requested_backend": requested_backend,
        "resolved_backend": backend.name,
        "resolution": resolution,
        "final_time": time,
        "steps": steps,
        "frames": len(frame_tuple),
        "maximum_progress": float(np.max(final_frame.progress)),
        "maximum_pressure": float(np.max(final_frame.pressure)),
        "minimum_velocity": float(np.min(final_frame.velocity)),
        "maximum_velocity": float(np.max(final_frame.velocity)),
        "note": (
            "A prescribed generic progress-rate field releases normalized heat. "
            "The EOS pressure gradient then accelerates the gas; no pressure "
            "body-force term is inserted."
        ),
    }
    (output_directory / "reactive_pressure_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
####


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "cupy"),
        default="auto",
    )
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--final-time", type=float, default=0.08)
    parser.add_argument("--frames", type=int, default=33)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("examples/backend_agnostic/reactive_pressure_run"),
    )
    arguments = parser.parse_args()
    run_demo(
        arguments.output,
        cast(BackendName, arguments.backend),
        resolution=arguments.resolution,
        final_time=arguments.final_time,
        snapshot_count=arguments.frames,
        fps=arguments.fps,
    )
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
