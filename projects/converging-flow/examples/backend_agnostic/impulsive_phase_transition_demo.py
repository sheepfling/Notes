"""Generate a generic feedback-driven source, pressure-wave, and phase-change study."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from numpy.typing import NDArray

from converging_flow.backend import Array, ArrayBackend, BackendName, get_array_backend
from converging_flow.example_runtime import capture_times, write_summary
from converging_flow.phase_euler import (
    PhaseEulerConfig,
    advance_impulsive_phase_euler_split,
    phase_conservative_to_primitive,
    phase_equilibrium_fraction,
    primitive_to_phase_conservative,
    stable_phase_timestep,
    validate_impulsive_event_history,
)
from converging_flow.recipes import PhaseThermalParameters, phase_impulse_config

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class PhaseFrame:
    time: float
    density: FloatArray
    velocity: FloatArray
    pressure: FloatArray
    activity: FloatArray
    phase_fraction: FloatArray
    phase_target: FloatArray
    phase_drive: FloatArray
    source_rate: FloatArray
####


def _capture_frame(
    time: float,
    state: Array,
    source_profile: Array,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> PhaseFrame:
    density, velocity, pressure, activity, phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
    )
    source_rate = (
        config.activity_growth_rate * source_profile * activity * (1.0 - activity)
    )
    phase_target = phase_equilibrium_fraction(
        pressure / (density * config.gas_constant),
        config,
        backend,
    )
    phase_drive = backend.xp.maximum(phase_target - phase_fraction, 0.0) / (
        config.phase_relaxation_time
    )
    return PhaseFrame(
        time=time,
        density=backend.to_numpy(density),
        velocity=backend.to_numpy(velocity[0]),
        pressure=backend.to_numpy(pressure),
        activity=backend.to_numpy(activity),
        phase_fraction=backend.to_numpy(phase_fraction),
        phase_target=backend.to_numpy(phase_target),
        phase_drive=backend.to_numpy(phase_drive),
        source_rate=backend.to_numpy(source_rate),
    )
####


def _temperature(
    frame: PhaseFrame,
    config: PhaseEulerConfig | None = None,
) -> FloatArray:
    gas_constant = 1.0 if config is None else config.gas_constant
    return frame.pressure / (frame.density * gas_constant)
####


def _pressure_acceleration(
    coordinate: FloatArray,
    frame: PhaseFrame,
) -> FloatArray:
    """Return the Euler pressure-gradient acceleration diagnostic ``-∂p/∂x / ρ``."""
    spacing = float(coordinate[1] - coordinate[0])
    return -np.gradient(frame.pressure, spacing, edge_order=1) / frame.density
####


def _save_final_profiles(
    coordinate: FloatArray,
    frame: PhaseFrame,
    config: PhaseEulerConfig,
    output_directory: Path,
) -> None:
    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    fields = (
        (frame.activity, "finite source progress"),
        (frame.pressure - 1.0, "pressure perturbation"),
        (frame.velocity, "material velocity"),
        (_temperature(frame, config), "ideal-gas temperature p/(ρR)"),
        (frame.phase_fraction, "transformed-phase fraction"),
        (frame.density, "density"),
    )
    for axes, (values, label) in zip(axes_grid.flat, fields, strict=True):
        axes.plot(coordinate, values)
        axes.set_title(label)
        axes.set_ylabel(label)
        axes.grid(True, alpha=0.25)
    ####
    for axes in axes_grid[-1, :]:
        axes.set_xlabel("position")
    ####
    figure.suptitle(
        "Impulsive source → thermal energy → EOS pressure → motion → phase transition"
    )
    figure.tight_layout()
    figure.savefig(output_directory / "impulsive_phase_profiles.png", dpi=180)
    plt.close(figure)
####


def _save_space_time(
    coordinate: FloatArray,
    frames: tuple[PhaseFrame, ...],
    config: PhaseEulerConfig,
    output_directory: Path,
) -> None:
    times = np.array([frame.time for frame in frames])
    fields = (
        (np.stack([frame.activity for frame in frames]), "source progress", 0.0, 1.0),
        (
            np.stack([frame.pressure - 1.0 for frame in frames]),
            "pressure perturbation",
            None,
            None,
        ),
        (
            np.stack([_temperature(frame, config) for frame in frames]),
            "ideal-gas temperature p/(ρR)",
            None,
            None,
        ),
        (
            np.stack([frame.phase_fraction for frame in frames]),
            "transformed-phase fraction",
            0.0,
            1.0,
        ),
        (
            np.stack([frame.phase_drive for frame in frames]),
            "phase-transition drive",
            0.0,
            None,
        ),
        (
            np.stack([frame.velocity for frame in frames]),
            "material velocity",
            None,
            None,
        ),
    )
    extent = (
        float(coordinate[0]),
        float(coordinate[-1]),
        float(times[0]),
        float(times[-1]),
    )
    figure, axes_grid = plt.subplots(len(fields), 1, figsize=(11, 15), sharex=True)
    for axes, (values, label, lower, upper) in zip(axes_grid, fields, strict=True):
        if label == "material velocity":
            bound = max(abs(float(np.min(values))), abs(float(np.max(values))))
            lower, upper = -bound, bound
        ####
        image = axes.imshow(
            values,
            origin="lower",
            extent=extent,
            aspect="auto",
            vmin=lower,
            vmax=upper,
        )
        axes.set_ylabel("time")
        axes.set_title(label)
        figure.colorbar(image, ax=axes, label=label)
    ####
    axes_grid[-1].set_xlabel("position")
    figure.suptitle("Generic impulsive event through space and time")
    figure.tight_layout()
    figure.savefig(output_directory / "impulsive_phase_space_time.png", dpi=180)
    plt.close(figure)
####


def _save_phase_response(
    coordinate: FloatArray,
    frames: tuple[PhaseFrame, ...],
    config: PhaseEulerConfig,
    output_directory: Path,
) -> None:
    """Show threshold, phase drive, and latent storage at peak conversion drive."""
    frame = max(frames, key=lambda item: float(np.sum(item.phase_drive)))
    temperature = _temperature(frame, config)
    latent_density = config.latent_heat_per_mass * frame.density * frame.phase_fraction
    figure, axes_grid = plt.subplots(2, 2, figsize=(14, 8), sharex=True)

    axes_grid[0, 0].plot(coordinate, temperature, label="temperature p/(ρR)")
    axes_grid[0, 0].axhline(
        config.transition_temperature,
        color="black",
        linestyle="--",
        label="transition threshold",
    )
    axes_grid[0, 0].set_title("Thermal threshold")
    axes_grid[0, 0].set_ylabel("temperature proxy")
    axes_grid[0, 0].legend()

    axes_grid[0, 1].plot(coordinate, frame.phase_fraction, label="current phase")
    axes_grid[0, 1].plot(
        coordinate,
        frame.phase_target,
        linestyle="--",
        label="temperature-equilibrium phase",
    )
    axes_grid[0, 1].set_title("Current and equilibrium phase fraction")
    axes_grid[0, 1].set_ylabel("phase fraction")
    axes_grid[0, 1].set_ylim(-0.03, 1.03)
    axes_grid[0, 1].legend()

    axes_grid[1, 0].plot(coordinate, frame.phase_drive)
    axes_grid[1, 0].set_title("One-way phase-transition drive")
    axes_grid[1, 0].set_ylabel("phase fraction / time")
    axes_grid[1, 0].set_xlabel("position")

    axes_grid[1, 1].plot(coordinate, latent_density)
    axes_grid[1, 1].set_title("Latent-energy storage density")
    axes_grid[1, 1].set_ylabel("normalized energy density")
    axes_grid[1, 1].set_xlabel("position")
    for axes in axes_grid.flat:
        axes.grid(True, alpha=0.25)
    ####
    figure.suptitle(f"Phase-transition response near peak drive | t = {frame.time:.4f}")
    figure.tight_layout()
    figure.savefig(output_directory / "impulsive_phase_response.png", dpi=180)
    plt.close(figure)
####


def _save_pressure_wave_diagnostics(
    coordinate: FloatArray,
    frames: tuple[PhaseFrame, ...],
    output_directory: Path,
) -> None:
    """Connect EOS pressure perturbation, acceleration, and material velocity."""
    frame = max(frames, key=lambda item: float(np.max(item.pressure)))
    acceleration = _pressure_acceleration(coordinate, frame)
    figure, axes_grid = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    axes_grid[0].plot(coordinate, frame.pressure - 1.0)
    axes_grid[0].set_title("EOS pressure perturbation")
    axes_grid[0].set_ylabel("Δp")
    axes_grid[1].plot(coordinate, acceleration)
    axes_grid[1].axhline(0.0, color="black", linewidth=0.8)
    axes_grid[1].set_title("Pressure-gradient acceleration")
    axes_grid[1].set_ylabel("−∂p/∂x / ρ")
    axes_grid[2].plot(coordinate, frame.velocity)
    axes_grid[2].axhline(0.0, color="black", linewidth=0.8)
    axes_grid[2].set_title("Resulting material velocity")
    axes_grid[2].set_ylabel("velocity")
    axes_grid[2].set_xlabel("position")
    for axes in axes_grid:
        axes.grid(True, alpha=0.25)
    ####
    figure.suptitle(
        f"Pressure-wave mechanics near peak pressure | t = {frame.time:.4f}"
    )
    figure.tight_layout()
    figure.savefig(output_directory / "impulsive_pressure_mechanics.png", dpi=180)
    plt.close(figure)
####


def _save_budgets(
    coordinate: FloatArray,
    frames: tuple[PhaseFrame, ...],
    config: PhaseEulerConfig,
    output_directory: Path,
) -> None:
    spacing = float(coordinate[1] - coordinate[0])
    times = np.array([frame.time for frame in frames])
    internal = np.array(
        [np.sum(frame.pressure / (config.gamma - 1.0)) * spacing for frame in frames]
    )
    kinetic = np.array(
        [
            np.sum(0.5 * frame.density * frame.velocity * frame.velocity) * spacing
            for frame in frames
        ]
    )
    initial_activity_mass = np.sum(frames[0].density * frames[0].activity) * spacing
    released = np.array(
        [
            config.heat_release_per_mass
            * (np.sum(frame.density * frame.activity) * spacing - initial_activity_mass)
            for frame in frames
        ]
    )
    latent = np.array(
        [
            config.latent_heat_per_mass
            * np.sum(frame.density * frame.phase_fraction)
            * spacing
            for frame in frames
        ]
    )
    phase_volume = np.array(
        [np.sum(frame.phase_fraction) * spacing for frame in frames]
    )
    total = internal + kinetic + latent
    residual = total - total[0] - released

    figure, axes_grid = plt.subplots(2, 2, figsize=(14, 9), sharex=True)
    axes_grid[0, 0].plot(times, released, label="released source energy")
    axes_grid[0, 0].plot(
        times, total - total[0], linestyle="--", label="total increase"
    )
    axes_grid[0, 0].set_title("Finite source reservoir and total energy")
    axes_grid[0, 0].set_ylabel("integrated normalized energy")
    axes_grid[0, 0].legend()

    axes_grid[0, 1].plot(times, internal, label="internal")
    axes_grid[0, 1].plot(times, kinetic, label="kinetic")
    axes_grid[0, 1].plot(times, latent, label="latent storage")
    axes_grid[0, 1].set_title("Energy partition")
    axes_grid[0, 1].set_ylabel("integrated normalized energy")
    axes_grid[0, 1].legend()

    axes_grid[1, 0].plot(times, phase_volume)
    axes_grid[1, 0].set_title("Transformed material amount")
    axes_grid[1, 0].set_ylabel("integrated phase fraction")
    axes_grid[1, 0].set_xlabel("time")

    axes_grid[1, 1].plot(times, residual)
    axes_grid[1, 1].axhline(0.0, color="black", linewidth=0.8)
    axes_grid[1, 1].set_title("Energy residual")
    axes_grid[1, 1].set_ylabel("total − initial − released")
    axes_grid[1, 1].set_xlabel("time")
    for axes in axes_grid.flat:
        axes.grid(True, alpha=0.25)
    ####
    figure.suptitle("Impulsive event and phase-transition budgets")
    figure.tight_layout()
    figure.savefig(output_directory / "impulsive_phase_budget.png", dpi=180)
    plt.close(figure)
####


def _save_animation(
    coordinate: FloatArray,
    frames: tuple[PhaseFrame, ...],
    config: PhaseEulerConfig,
    output_directory: Path,
    fps: int,
) -> None:
    pressure = np.stack([frame.pressure - 1.0 for frame in frames])
    temperature = np.stack([_temperature(frame, config) for frame in frames])
    velocity = np.stack([frame.velocity for frame in frames])
    pressure_bounds = (float(np.min(pressure)), float(np.max(pressure)))
    temperature_bounds = (float(np.min(temperature)), float(np.max(temperature)))
    velocity_bound = max(abs(float(np.min(velocity))), abs(float(np.max(velocity))))

    phase_drive = np.stack([frame.phase_drive for frame in frames])
    figure, axes_grid = plt.subplots(6, 1, figsize=(10, 14), sharex=True)
    lines = (
        axes_grid[0].plot(coordinate, frames[0].activity)[0],
        axes_grid[1].plot(coordinate, pressure[0])[0],
        axes_grid[2].plot(coordinate, temperature[0])[0],
        axes_grid[3].plot(coordinate, frames[0].phase_fraction)[0],
        axes_grid[4].plot(coordinate, phase_drive[0])[0],
        axes_grid[5].plot(coordinate, frames[0].velocity)[0],
    )
    labels = (
        "source progress",
        "pressure perturbation",
        "ideal-gas temperature p/(ρR)",
        "transformed phase fraction",
        "phase-transition drive",
        "material velocity",
    )
    bounds = (
        (0.0, 1.0),
        pressure_bounds,
        temperature_bounds,
        (0.0, 1.0),
        (0.0, float(np.max(phase_drive))),
        (-velocity_bound, velocity_bound),
    )
    for axes, label, limits in zip(axes_grid, labels, bounds, strict=True):
        axes.set_ylabel(label)
        axes.set_ylim(*limits)
        axes.grid(True, alpha=0.25)
    ####
    axes_grid[-1].set_xlabel("position")

    def update(index: int) -> tuple[object, ...]:
        frame = frames[index]
        lines[0].set_ydata(frame.activity)
        lines[1].set_ydata(frame.pressure - 1.0)
        lines[2].set_ydata(_temperature(frame, config))
        lines[3].set_ydata(frame.phase_fraction)
        lines[4].set_ydata(frame.phase_drive)
        lines[5].set_ydata(frame.velocity)
        figure.suptitle(f"Generic impulsive phase transition | t = {frame.time:.4f}")
        return lines
    ####

    animation = FuncAnimation(
        figure, update, frames=len(frames), interval=1000 / fps, blit=False
    )
    figure.tight_layout()
    animation.save(
        output_directory / "impulsive_phase_evolution.gif",
        writer=PillowWriter(fps=fps),
        dpi=120,
    )
    plt.close(figure)
####


def _save_pressure_wave_animation(
    coordinate: FloatArray,
    frames: tuple[PhaseFrame, ...],
    output_directory: Path,
    fps: int,
) -> None:
    """Animate the pressure-to-acceleration-to-velocity chain on fixed scales."""
    pressure = np.stack([frame.pressure - 1.0 for frame in frames])
    acceleration = np.stack(
        [_pressure_acceleration(coordinate, frame) for frame in frames]
    )
    velocity = np.stack([frame.velocity for frame in frames])
    acceleration_bound = max(
        abs(float(np.min(acceleration))), abs(float(np.max(acceleration)))
    )
    velocity_bound = max(abs(float(np.min(velocity))), abs(float(np.max(velocity))))
    figure, axes_grid = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    lines = (
        axes_grid[0].plot(coordinate, pressure[0])[0],
        axes_grid[1].plot(coordinate, acceleration[0])[0],
        axes_grid[2].plot(coordinate, velocity[0])[0],
    )
    labels = ("pressure perturbation", "−∂p/∂x / ρ", "material velocity")
    limits = (
        (float(np.min(pressure)), float(np.max(pressure))),
        (-acceleration_bound, acceleration_bound),
        (-velocity_bound, velocity_bound),
    )
    for axes, label, bounds in zip(axes_grid, labels, limits, strict=True):
        axes.set_ylabel(label)
        axes.set_ylim(*bounds)
        axes.grid(True, alpha=0.25)
    ####
    axes_grid[-1].set_xlabel("position")

    def update(index: int) -> tuple[object, ...]:
        lines[0].set_ydata(pressure[index])
        lines[1].set_ydata(acceleration[index])
        lines[2].set_ydata(velocity[index])
        figure.suptitle(f"EOS pressure-wave mechanics | t = {frames[index].time:.4f}")
        return lines
    ####

    animation = FuncAnimation(
        figure, update, frames=len(frames), interval=1000 / fps, blit=False
    )
    figure.tight_layout()
    animation.save(
        output_directory / "impulsive_pressure_wave_evolution.gif",
        writer=PillowWriter(fps=fps),
        dpi=120,
    )
    plt.close(figure)
####


def run_demo(
    output_directory: Path,
    requested_backend: BackendName,
    resolution: int = 768,
    final_time: float = 0.18,
    snapshot_count: int = 121,
    fps: int = 18,
    thermal_parameters: PhaseThermalParameters | None = None,
    source_width: float = 0.13,
) -> None:
    if resolution < 16:
        raise ValueError("resolution must be at least 16")
    ####
    if final_time <= 0.0:
        raise ValueError("final_time must be positive")
    ####
    if snapshot_count < 2:
        raise ValueError("snapshot_count must be at least two")
    ####
    backend = get_array_backend(requested_backend)
    config = phase_impulse_config(thermal_parameters)
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
    source_profile = backend.xp.exp(-0.5 * (coordinate / source_width) ** 2)
    source_profile *= 1.0 + 0.30 * backend.xp.tanh((coordinate + 0.08) / 0.06)
    activity = 0.015 * source_profile
    phase_fraction = backend.xp.zeros(resolution, dtype=np.float64)
    state = primitive_to_phase_conservative(
        density,
        velocity,
        pressure,
        activity,
        phase_fraction,
        config,
        backend,
    )

    target_times = capture_times(final_time, snapshot_count)
    frames: list[PhaseFrame] = [
        _capture_frame(0.0, state, source_profile, config, backend)
    ]
    next_target = 1
    time = 0.0
    steps = 0
    while time < final_time:
        timestep = min(
            stable_phase_timestep(
                state, spacing, cfl=0.26, config=config, backend=backend
            ),
            2.0e-4,
            final_time - time,
        )
        state = advance_impulsive_phase_euler_split(
            state,
            source_profile,
            timestep,
            spacing,
            config,
            backend,
        )
        time += timestep
        steps += 1
        while (
            next_target < snapshot_count and time >= target_times[next_target] - 1.0e-14
        ):
            frames.append(_capture_frame(time, state, source_profile, config, backend))
            next_target += 1
        ####
    ####

    backend.synchronize()
    frame_tuple = tuple(frames)
    final_frame = frame_tuple[-1]
    validation = validate_impulsive_event_history(
        coordinate_numpy,
        np.array([frame.time for frame in frame_tuple]),
        np.stack([frame.density for frame in frame_tuple]),
        np.stack([frame.velocity for frame in frame_tuple]),
        np.stack([frame.pressure for frame in frame_tuple]),
        np.stack([frame.activity for frame in frame_tuple]),
        np.stack([frame.phase_fraction for frame in frame_tuple]),
        config,
    )
    if not validation.passed:
        raise RuntimeError(
            "impulsive phase-transition scenario did not meet its expected "
            f"validation checks: {validation}"
        )
    ####
    output_directory.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_directory / "impulsive_phase_state.npz",
        coordinate=coordinate_numpy,
        time=np.array(time),
        steps=np.array(steps),
        frame_time=np.array([frame.time for frame in frame_tuple]),
        frame_density=np.stack([frame.density for frame in frame_tuple]),
        frame_velocity=np.stack([frame.velocity for frame in frame_tuple]),
        frame_pressure=np.stack([frame.pressure for frame in frame_tuple]),
        frame_activity=np.stack([frame.activity for frame in frame_tuple]),
        frame_phase_fraction=np.stack([frame.phase_fraction for frame in frame_tuple]),
        frame_phase_target=np.stack([frame.phase_target for frame in frame_tuple]),
        frame_phase_drive=np.stack([frame.phase_drive for frame in frame_tuple]),
        frame_source_rate=np.stack([frame.source_rate for frame in frame_tuple]),
    )
    _save_final_profiles(coordinate_numpy, final_frame, config, output_directory)
    _save_space_time(coordinate_numpy, frame_tuple, config, output_directory)
    _save_phase_response(coordinate_numpy, frame_tuple, config, output_directory)
    _save_pressure_wave_diagnostics(coordinate_numpy, frame_tuple, output_directory)
    _save_budgets(coordinate_numpy, frame_tuple, config, output_directory)
    _save_animation(coordinate_numpy, frame_tuple, config, output_directory, fps)
    _save_pressure_wave_animation(
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
        "thermal_model": asdict(config),
        "maximum_pressure": float(np.max(final_frame.pressure)),
        "maximum_temperature_proxy": float(np.max(_temperature(final_frame, config))),
        "maximum_phase_fraction": float(np.max(final_frame.phase_fraction)),
        "minimum_velocity": float(np.min(final_frame.velocity)),
        "maximum_velocity": float(np.max(final_frame.velocity)),
        "scenario_validation": asdict(validation),
        "scenario_validation_passed": validation.passed,
        "model_note": (
            "Normalized finite feedback source with Euler pressure-driven motion and "
            "an irreversible latent-heat phase fraction. It is not calibrated to a "
            "specific substance or operating system."
        ),
    }
    write_summary(output_directory / "impulsive_phase_summary.json", summary)
####


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("auto", "numpy", "cupy"), default="auto")
    parser.add_argument("--resolution", type=int, default=768)
    parser.add_argument("--final-time", type=float, default=0.18)
    parser.add_argument("--frames", type=int, default=121)
    parser.add_argument("--fps", type=int, default=18)
    parser.add_argument("--specific-heat", type=float, default=2.5)
    parser.add_argument("--gas-constant", type=float, default=1.0)
    parser.add_argument("--heat-release-per-mass", type=float, default=6.0)
    parser.add_argument("--activity-growth-rate", type=float, default=75.0)
    parser.add_argument("--phase-change-energy-per-mass", type=float, default=1.0)
    parser.add_argument("--transition-temperature", type=float, default=2.0)
    parser.add_argument("--transition-width", type=float, default=0.08)
    parser.add_argument("--phase-relaxation-time", type=float, default=0.012)
    parser.add_argument("--source-width", type=float, default=0.13)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/converging-flow/impulsive-phase-transition"),
    )
    arguments = parser.parse_args()
    run_demo(
        arguments.output,
        cast(BackendName, arguments.backend),
        resolution=arguments.resolution,
        final_time=arguments.final_time,
        snapshot_count=arguments.frames,
        fps=arguments.fps,
        thermal_parameters=PhaseThermalParameters(
            specific_heat=arguments.specific_heat,
            gas_constant=arguments.gas_constant,
            heat_release_per_mass=arguments.heat_release_per_mass,
            activity_growth_rate=arguments.activity_growth_rate,
            phase_change_energy_per_mass=arguments.phase_change_energy_per_mass,
            transition_temperature=arguments.transition_temperature,
            transition_width=arguments.transition_width,
            phase_relaxation_time=arguments.phase_relaxation_time,
        ),
        source_width=arguments.source_width,
    )
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
