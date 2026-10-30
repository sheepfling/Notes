"""Run a settled channel-block precursor followed by a generic 2D Euler event.

The scalar channel-block model supplies a normalized source-permission map to a
separate Euler-plus-phase solver. This is a staged visualization handoff, not a
calibrated multiphysics material model.
"""

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
from matplotlib.image import AxesImage
from numpy.typing import NDArray

from converging_flow.backend import Array, ArrayBackend, BackendName, get_array_backend
from converging_flow.coupling import NormalizedWeightedCoupling
from converging_flow.example_runtime import capture_times, write_summary
from converging_flow.phase_euler import (
    PhaseEulerConfig,
    advance_impulsive_phase_euler_split,
    phase_conservative_to_primitive,
    primitive_to_phase_conservative,
    stable_phase_timestep,
)
from converging_flow.radiant_wave import (
    CHANNEL_ID,
    NEUTRAL_ID,
    RadiantWaveConfig,
    run_radiant_wave,
)
from converging_flow.recipes import perforated_block_regulation_config

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class EventFrame:
    time: float
    density: FloatArray
    velocity: FloatArray
    pressure: FloatArray
    activity: FloatArray
    phase_fraction: FloatArray
####


def _channel_block_config(resolution: int, backend: BackendName) -> RadiantWaveConfig:
    return perforated_block_regulation_config(
        resolution,
        backend,
        final_time=0.24,
        source_scale=0.5,
    )
####


def _capture_frame(
    time: float,
    state: Array,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
) -> EventFrame:
    density, velocity, pressure, activity, phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
    )
    return EventFrame(
        time=time,
        density=backend.to_numpy(density),
        velocity=backend.to_numpy(velocity),
        pressure=backend.to_numpy(pressure),
        activity=backend.to_numpy(activity),
        phase_fraction=backend.to_numpy(phase_fraction),
    )
####


def _event_handoff(
    precursor_resolution: int,
    backend: BackendName,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]:
    """Reduce settled 3D fields to a 2D impulse-permission cross-section."""
    precursor = run_radiant_wave(
        _channel_block_config(precursor_resolution, backend),
        snapshot_count=9,
    )
    active_fraction = np.mean(precursor.materials.material_id == NEUTRAL_ID, axis=2)
    channel_fraction = np.mean(precursor.materials.material_id == CHANNEL_ID, axis=2)
    activity = np.mean(precursor.activity, axis=2)
    heat = np.mean(precursor.heat, axis=2)
    coordinate = precursor.coordinates[0]
    x, y = np.meshgrid(coordinate, coordinate, indexing="ij")
    central_impulse = np.exp(-0.5 * (x * x + y * y) / 0.15**2)
    source_permission = NormalizedWeightedCoupling(
        weights=(("activity", 0.45), ("heat", 0.30)),
        baseline=0.25,
    ).apply(
        {"activity": activity, "heat": heat},
        envelope=central_impulse * active_fraction,
    )
    return active_fraction, channel_fraction, activity, heat, source_permission
####


def _save_handoff(
    coordinate: FloatArray,
    active_fraction: FloatArray,
    channel_fraction: FloatArray,
    activity: FloatArray,
    heat: FloatArray,
    source_permission: FloatArray,
    output_directory: Path,
) -> None:
    extent = (
        float(coordinate[0]),
        float(coordinate[-1]),
        float(coordinate[0]),
        float(coordinate[-1]),
    )
    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    fields = (
        (active_fraction, "settled reactive-medium axial fraction"),
        (channel_fraction, "open/loss-channel axial fraction"),
        (activity, "settled activity average"),
        (heat, "settled heat average"),
        (source_permission, "state-derived impulse permission"),
    )
    for axes, (values, label) in zip(axes_grid.flat, fields, strict=False):
        image = axes.imshow(values.T, origin="lower", extent=extent, aspect="equal")
        axes.set_title(label)
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        figure.colorbar(image, ax=axes, shrink=0.82)
    ####
    axes_grid.flat[-1].axis("off")
    figure.suptitle("Settled 3D channel-block state → 2D Euler impulse handoff")
    figure.savefig(output_directory / "channel_event_handoff.png", dpi=180)
    plt.close(figure)
####


def _save_final_fields(
    coordinate: FloatArray,
    frame: EventFrame,
    source_permission: FloatArray,
    output_directory: Path,
) -> None:
    extent = (
        float(coordinate[0]),
        float(coordinate[-1]),
        float(coordinate[0]),
        float(coordinate[-1]),
    )
    speed = np.sqrt(np.sum(frame.velocity * frame.velocity, axis=0))
    fields = (
        (source_permission, "state-derived impulse permission"),
        (frame.activity, "finite source progress"),
        (frame.pressure - 1.0, "EOS pressure perturbation"),
        (frame.pressure / frame.density, "temperature proxy p/ρ"),
        (frame.phase_fraction, "transformed-phase fraction"),
        (speed, "material speed"),
    )
    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    for axes, (values, label) in zip(axes_grid.flat, fields, strict=True):
        image = axes.imshow(values.T, origin="lower", extent=extent, aspect="equal")
        axes.set_title(label)
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        figure.colorbar(image, ax=axes, shrink=0.82)
    ####
    figure.suptitle(
        f"2D impulsive event after channel-block regulation | t = {frame.time:.4f}"
    )
    figure.savefig(output_directory / "channel_event_final_fields.png", dpi=180)
    plt.close(figure)
####


def _save_animation(
    coordinate: FloatArray,
    frames: tuple[EventFrame, ...],
    source_permission: FloatArray,
    output_directory: Path,
    fps: int,
) -> None:
    extent = (
        float(coordinate[0]),
        float(coordinate[-1]),
        float(coordinate[0]),
        float(coordinate[-1]),
    )
    pressure = np.stack([frame.pressure - 1.0 for frame in frames])
    temperature = np.stack([frame.pressure / frame.density for frame in frames])
    phase = np.stack([frame.phase_fraction for frame in frames])
    speed = np.stack(
        [np.sqrt(np.sum(frame.velocity * frame.velocity, axis=0)) for frame in frames]
    )
    fields = (
        (
            source_permission,
            "source permission",
            (0.0, float(np.max(source_permission))),
        ),
        (
            pressure[0],
            "pressure perturbation",
            (float(np.min(pressure)), float(np.max(pressure))),
        ),
        (
            temperature[0],
            "temperature proxy p/ρ",
            (float(np.min(temperature)), float(np.max(temperature))),
        ),
        (phase[0], "phase fraction", (0.0, 1.0)),
        (speed[0], "material speed", (0.0, float(np.max(speed)))),
    )
    figure, axes_grid = plt.subplots(1, 5, figsize=(22, 5), constrained_layout=True)
    images: list[AxesImage] = []
    for axes, (values, label, bounds) in zip(axes_grid, fields, strict=True):
        image = axes.imshow(
            values.T,
            origin="lower",
            extent=extent,
            aspect="equal",
            vmin=bounds[0],
            vmax=bounds[1],
        )
        axes.set_title(label)
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        figure.colorbar(image, ax=axes, shrink=0.80)
        images.append(image)
    ####

    def update(index: int) -> tuple[AxesImage, ...]:
        images[1].set_data(pressure[index].T)
        images[2].set_data(temperature[index].T)
        images[3].set_data(phase[index].T)
        images[4].set_data(speed[index].T)
        figure.suptitle(
            f"Channel-shaped 2D impulsive event | t = {frames[index].time:.4f}"
        )
        return tuple(images)
    ####

    animation = FuncAnimation(
        figure, update, frames=len(frames), interval=1000 / fps, blit=False
    )
    animation.save(
        output_directory / "channel_event_evolution.gif",
        writer=PillowWriter(fps=fps),
        dpi=110,
    )
    plt.close(figure)
####


def _event_validation(frames: tuple[EventFrame, ...]) -> dict[str, bool | float]:
    pressure_rise = max(float(np.max(frame.pressure)) for frame in frames) - 1.0
    phase_peak = max(float(np.max(frame.phase_fraction)) for frame in frames)
    speeds = [
        np.sqrt(np.sum(frame.velocity * frame.velocity, axis=0)) for frame in frames
    ]
    maximum_speed = max(float(np.max(speed)) for speed in speeds)
    finite = all(
        np.all(np.isfinite(values))
        for frame in frames
        for values in (
            frame.density,
            frame.velocity,
            frame.pressure,
            frame.activity,
            frame.phase_fraction,
        )
    )
    bounded = all(
        np.all((frame.activity >= 0.0) & (frame.activity <= 1.0))
        and np.all((frame.phase_fraction >= 0.0) & (frame.phase_fraction <= 1.0))
        for frame in frames
    )
    return {
        "finite_fields": finite,
        "bounded_source_and_phase": bounded,
        "pressure_wave_forms": pressure_rise > 0.10,
        "phase_transition_occurs": phase_peak > 0.50,
        "material_motion_forms": maximum_speed > 0.05,
        "maximum_pressure_rise": pressure_rise,
        "maximum_phase_fraction": phase_peak,
        "maximum_speed": maximum_speed,
    }
####


def run_demo(
    output_directory: Path,
    requested_backend: BackendName,
    precursor_resolution: int = 40,
    event_resolution: int = 64,
    event_final_time: float = 0.16,
    frames: int = 101,
    fps: int = 16,
) -> None:
    if precursor_resolution < 24 or event_resolution < 24:
        raise ValueError("both resolutions must be at least 24")
    ####
    if frames < 2 or fps < 1 or event_final_time <= 0.0:
        raise ValueError(
            "event time must be positive, with at least two frames and positive fps"
        )
    ####
    output_directory.mkdir(parents=True, exist_ok=True)
    active_fraction, channel_fraction, activity, heat, source_permission = (
        _event_handoff(
            precursor_resolution,
            requested_backend,
        )
    )
    source_permission = np.array(source_permission, copy=True)
    source_permission /= max(float(np.max(source_permission)), 1.0e-12)
    coordinate = np.linspace(
        -1.0 + 1.0 / event_resolution, 1.0 - 1.0 / event_resolution, event_resolution
    )
    if precursor_resolution != event_resolution:
        raise ValueError(
            "use equal precursor and event resolutions for the direct 2D handoff"
        )
    ####
    _save_handoff(
        coordinate,
        active_fraction,
        channel_fraction,
        activity,
        heat,
        source_permission,
        output_directory,
    )

    backend = get_array_backend(requested_backend)
    config = PhaseEulerConfig(
        heat_release_per_mass=8.0,
        activity_growth_rate=90.0,
        latent_heat_per_mass=1.2,
        transition_temperature=2.2,
        transition_width=0.08,
        phase_relaxation_time=0.012,
    )
    source = backend.asarray(source_permission)
    density = backend.xp.ones((event_resolution, event_resolution), dtype=np.float64)
    velocity = backend.xp.zeros(
        (2, event_resolution, event_resolution), dtype=np.float64
    )
    pressure = backend.xp.ones((event_resolution, event_resolution), dtype=np.float64)
    activity_seed = 0.015 * source
    phase = backend.xp.zeros_like(source)
    state = primitive_to_phase_conservative(
        density, velocity, pressure, activity_seed, phase, config, backend
    )
    spacing = (2.0 / event_resolution, 2.0 / event_resolution)
    target_times = capture_times(event_final_time, frames)
    captured: list[EventFrame] = [_capture_frame(0.0, state, config, backend)]
    next_target = 1
    time = 0.0
    steps = 0
    while time < event_final_time:
        timestep = min(
            stable_phase_timestep(state, spacing, 0.24, config, backend),
            2.0e-4,
            event_final_time - time,
        )
        state = advance_impulsive_phase_euler_split(
            state, source, timestep, spacing, config, backend
        )
        time += timestep
        steps += 1
        while next_target < frames and time >= target_times[next_target] - 1.0e-14:
            captured.append(_capture_frame(time, state, config, backend))
            next_target += 1
        ####
    ####
    backend.synchronize()
    frame_tuple = tuple(captured)
    validation = _event_validation(frame_tuple)
    if not all(value for key, value in validation.items() if isinstance(value, bool)):
        raise RuntimeError(
            f"channel-block impulsive event validation failed: {validation}"
        )
    ####
    final_frame = frame_tuple[-1]
    _save_final_fields(coordinate, final_frame, source_permission, output_directory)
    _save_animation(coordinate, frame_tuple, source_permission, output_directory, fps)
    np.savez_compressed(
        output_directory / "channel_event_state.npz",
        coordinate=coordinate,
        source_permission=source_permission,
        frame_time=np.array([frame.time for frame in frame_tuple]),
        frame_density=np.stack([frame.density for frame in frame_tuple]),
        frame_velocity=np.stack([frame.velocity for frame in frame_tuple]),
        frame_pressure=np.stack([frame.pressure for frame in frame_tuple]),
        frame_activity=np.stack([frame.activity for frame in frame_tuple]),
        frame_phase_fraction=np.stack([frame.phase_fraction for frame in frame_tuple]),
    )
    summary = {
        "requested_backend": requested_backend,
        "resolved_backend": backend.name,
        "precursor_resolution": precursor_resolution,
        "event_resolution": event_resolution,
        "event_final_time": time,
        "event_steps": steps,
        "frames": len(frame_tuple),
        "thermal_model": asdict(config),
        "event_validation": validation,
        "model_note": "A settled scalar channel-block state shapes the 2D Euler source field. The Euler continuum remains homogeneous and normalized; the handoff is illustrative rather than a calibrated material coupling.",
    }
    write_summary(output_directory / "channel_event_summary.json", summary)
####


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a channel-block-to-impulsive-event visualization"
    )
    parser.add_argument("--backend", choices=("auto", "numpy", "cupy"), default="auto")
    parser.add_argument(
        "--resolution",
        type=int,
        default=48,
        help="shared precursor and Euler grid resolution",
    )
    parser.add_argument("--final-time", type=float, default=0.16)
    parser.add_argument("--frames", type=int, default=101)
    parser.add_argument("--fps", type=int, default=16)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/converging-flow/channel-block-impulsive-event"),
    )
    arguments = parser.parse_args()
    run_demo(
        arguments.output,
        cast(BackendName, arguments.backend),
        arguments.resolution,
        arguments.resolution,
        arguments.final_time,
        arguments.frames,
        arguments.fps,
    )
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
