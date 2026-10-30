"""Run a settled 3D perforated block followed by a localized 3D Euler event.

The scalar-wave precursor and the Euler-plus-phase response remain distinct
normalized models.  The precursor's settled activity, heat, wave-pressure
proxy, and material map create an event-permission field on the same 3D grid.
The Euler stage then computes its own thermodynamic pressure, temperature,
velocity, and phase response.
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
from converging_flow.material_events import LinearRamp
from converging_flow.phase_euler import (
    PhaseEulerConfig,
    advance_impulsive_phase_euler_split,
    phase_conservative_to_primitive,
    primitive_to_phase_conservative,
    stable_phase_timestep,
)
from converging_flow.radiant_wave import NEUTRAL_ID, RadiantWaveResult, run_radiant_wave
from converging_flow.recipes import (
    CouplingParameters,
    EventFootprintParameters,
    EventValidationParameters,
    PerforatedBlockEventParameters,
    PerforatedBlockParameters,
    PresentationParameters,
    perforated_block_event_parameters_from_file,
    perforated_block_regulation_config,
    phase_impulse_config,
)

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class EventPlaneFrame:
    """A compact, event-aligned 2D slice plus global 3D extrema."""

    time: float
    density: FloatArray
    pressure: FloatArray
    temperature: FloatArray
    activity: FloatArray
    phase_fraction: FloatArray
    speed: FloatArray
    maximum_pressure: float
    maximum_temperature: float
    maximum_phase_fraction: float
    maximum_speed: float
####


def _normalized(values: FloatArray) -> FloatArray:
    return values / max(float(np.max(np.abs(values))), 1.0e-12)
####


def _event_permission(
    precursor: RadiantWaveResult,
    center: tuple[float, float, float],
    width: float,
    coupling: CouplingParameters,
) -> FloatArray:
    if width <= 0.0:
        raise ValueError("event width must be positive")
    ####
    x, y, z = np.meshgrid(*precursor.coordinates, indexing="ij", sparse=True)
    footprint = np.exp(
        -0.5
        * ((x - center[0]) ** 2 + (y - center[1]) ** 2 + (z - center[2]) ** 2)
        / width**2
    )
    active_medium = (precursor.materials.material_id == NEUTRAL_ID).astype(np.float64)
    return NormalizedWeightedCoupling(
        weights=(
            ("settled activity", coupling.activity_weight),
            ("settled heat", coupling.heat_weight),
            ("settled wave pressure proxy", coupling.wave_pressure_weight),
        ),
        baseline=coupling.baseline,
    ).apply(
        {
            "settled activity": precursor.activity,
            "settled heat": precursor.heat,
            "settled wave pressure proxy": precursor.wave_pressure,
        },
        envelope=footprint * active_medium,
    )
####


def _event_plane_index(permission: FloatArray) -> int:
    return int(np.unravel_index(int(np.argmax(permission)), permission.shape)[2])
####


def _capture_plane_frame(
    time: float,
    state: Array,
    config: PhaseEulerConfig,
    backend: ArrayBackend,
    z_index: int,
) -> EventPlaneFrame:
    density, velocity, pressure, activity, phase_fraction = (
        phase_conservative_to_primitive(state, config, backend)
    )
    temperature = pressure / density
    speed = backend.xp.sqrt(backend.xp.sum(velocity * velocity, axis=0))
    return EventPlaneFrame(
        time=time,
        density=backend.to_numpy(density[:, :, z_index]),
        pressure=backend.to_numpy(pressure[:, :, z_index]),
        temperature=backend.to_numpy(temperature[:, :, z_index]),
        activity=backend.to_numpy(activity[:, :, z_index]),
        phase_fraction=backend.to_numpy(phase_fraction[:, :, z_index]),
        speed=backend.to_numpy(speed[:, :, z_index]),
        maximum_pressure=backend.scalar(backend.xp.max(pressure)),
        maximum_temperature=backend.scalar(backend.xp.max(temperature)),
        maximum_phase_fraction=backend.scalar(backend.xp.max(phase_fraction)),
        maximum_speed=backend.scalar(backend.xp.max(speed)),
    )
####


def _extent(coordinate: FloatArray) -> tuple[float, float, float, float]:
    return (
        float(coordinate[0]),
        float(coordinate[-1]),
        float(coordinate[0]),
        float(coordinate[-1]),
    )
####


def _save_handoff(
    coordinate: FloatArray,
    z_value: float,
    precursor: RadiantWaveResult,
    permission: FloatArray,
    initial_pressure: FloatArray,
    z_index: int,
    output_directory: Path,
) -> None:
    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    fields = (
        (precursor.materials.material_id[:, :, z_index], "settled material map"),
        (precursor.activity[:, :, z_index], "settled activity"),
        (precursor.heat[:, :, z_index], "settled heat"),
        (precursor.wave_pressure[:, :, z_index], "scalar wave-pressure proxy"),
        (permission[:, :, z_index], "localized event permission"),
        (initial_pressure[:, :, z_index] - 1.0, "Euler initial pressure offset"),
    )
    for axes, (values, label) in zip(axes_grid.flat, fields, strict=True):
        image = axes.imshow(
            values.T,
            origin="lower",
            extent=_extent(coordinate),
            aspect="equal",
        )
        axes.set_title(label)
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        figure.colorbar(image, ax=axes, shrink=0.82)
    ####
    figure.suptitle(
        "Settled 3D perforated-block state → localized 3D Euler event "
        f"(z = {z_value:.3f})"
    )
    figure.savefig(output_directory / "perforated_event_handoff.png", dpi=180)
    plt.close(figure)
####


def _save_final_fields(
    coordinate: FloatArray,
    z_value: float,
    permission: FloatArray,
    initial_pressure: FloatArray,
    final: EventPlaneFrame,
    z_index: int,
    output_directory: Path,
) -> None:
    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    fields = (
        (permission[:, :, z_index], "localized event permission"),
        (final.pressure - initial_pressure[:, :, z_index], "EOS pressure rise"),
        (final.temperature, "temperature proxy"),
        (final.activity, "finite source progress"),
        (final.phase_fraction, "transformed phase fraction"),
        (final.speed, "material speed"),
    )
    for axes, (values, label) in zip(axes_grid.flat, fields, strict=True):
        image = axes.imshow(
            values.T,
            origin="lower",
            extent=_extent(coordinate),
            aspect="equal",
        )
        axes.set_title(label)
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        figure.colorbar(image, ax=axes, shrink=0.82)
    ####
    figure.suptitle(
        "3D finite event response after perforated-block regulation "
        f"(z = {z_value:.3f}, t = {final.time:.4f})"
    )
    figure.savefig(output_directory / "perforated_event_final_fields.png", dpi=180)
    plt.close(figure)
####


def _save_animation(
    coordinate: FloatArray,
    frames: tuple[EventPlaneFrame, ...],
    permission: FloatArray,
    initial_pressure: FloatArray,
    z_index: int,
    output_directory: Path,
    fps: int,
) -> None:
    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    pressure_rises = [
        frame.pressure - initial_pressure[:, :, z_index] for frame in frames
    ]
    fields = (
        ([permission[:, :, z_index]] * len(frames), "event permission"),
        (pressure_rises, "EOS pressure rise"),
        ([frame.temperature for frame in frames], "temperature proxy"),
        ([frame.activity for frame in frames], "finite source progress"),
        ([frame.phase_fraction for frame in frames], "transformed phase fraction"),
        ([frame.speed for frame in frames], "material speed"),
    )
    images: list[AxesImage] = []
    for axes, (values, label) in zip(axes_grid.flat, fields, strict=True):
        lower = min(float(np.min(value)) for value in values)
        upper = max(float(np.max(value)) for value in values)
        if lower == upper:
            upper = lower + 1.0
        ####
        image = axes.imshow(
            values[0].T,
            origin="lower",
            extent=_extent(coordinate),
            aspect="equal",
            vmin=lower,
            vmax=upper,
        )
        axes.set_title(label)
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        figure.colorbar(image, ax=axes, shrink=0.82)
        images.append(image)
    ####

    def update(index: int) -> tuple[AxesImage, ...]:
        for image, (values, _label) in zip(images, fields, strict=True):
            image.set_data(values[index].T)
        ####
        figure.suptitle(
            "Localized 3D finite event after regulated perforated-block stage "
            f"| event t = {frames[index].time:.4f}"
        )
        return tuple(images)
    ####

    animation = FuncAnimation(
        figure,
        update,
        frames=len(frames),
        interval=1000 / fps,
        blit=False,
    )
    animation.save(
        output_directory / "perforated_event_evolution.gif",
        writer=PillowWriter(fps=fps),
        dpi=120,
    )
    plt.close(figure)
####


def _save_stage_history(
    precursor: RadiantWaveResult,
    event_frames: tuple[EventPlaneFrame, ...],
    event_start_time: float,
    output_directory: Path,
) -> None:
    figure, axes_grid = plt.subplots(3, 1, figsize=(11, 10), sharex=False)
    precursor_times = np.array([frame.time for frame in precursor.frames])
    balance = np.array([frame.budget.balance_factor for frame in precursor.frames])
    heat = np.array([frame.budget.thermal_energy for frame in precursor.frames])
    wave_pressure = np.array(
        [float(np.max(frame.wave_pressure)) for frame in precursor.frames]
    )
    axes_grid[0].plot(precursor_times, balance, label="source-to-loss balance factor")
    axes_grid[0].axhline(1.0, color="black", linewidth=0.8)
    axes_grid[0].set_ylabel("normalized ratio")
    axes_grid[0].set_title("Stage 1: perforated-block regulation")
    axes_grid[0].legend()
    axes_grid[0].grid(True, alpha=0.25)

    axes_grid[1].plot(precursor_times, heat, label="stored thermal field")
    wave_axes = axes_grid[1].twinx()
    wave_axes.plot(
        precursor_times,
        wave_pressure,
        color="tab:orange",
        label="maximum wave-pressure proxy",
    )
    axes_grid[1].set_xlabel("precursor time")
    axes_grid[1].set_ylabel("stored thermal field")
    wave_axes.set_ylabel("wave-pressure proxy")
    lines, labels = axes_grid[1].get_legend_handles_labels()
    wave_lines, wave_labels = wave_axes.get_legend_handles_labels()
    axes_grid[1].legend(lines + wave_lines, labels + wave_labels)
    axes_grid[1].grid(True, alpha=0.25)

    event_times = np.array([frame.time for frame in event_frames])
    axes_grid[2].plot(
        event_times,
        [frame.maximum_pressure for frame in event_frames],
        label="maximum EOS pressure",
    )
    axes_grid[2].plot(
        event_times,
        [frame.maximum_temperature for frame in event_frames],
        label="maximum temperature",
    )
    axes_grid[2].plot(
        event_times,
        [frame.maximum_phase_fraction for frame in event_frames],
        label="maximum phase fraction",
    )
    axes_grid[2].plot(
        event_times,
        [frame.maximum_speed for frame in event_frames],
        label="maximum speed",
    )
    axes_grid[2].axvline(
        event_start_time, color="black", linestyle="--", label="event enabled"
    )
    axes_grid[2].set_xlabel("Euler event time")
    axes_grid[2].set_ylabel("normalized field extrema")
    axes_grid[2].set_title("Stage 2: finite localized pressure and phase response")
    axes_grid[2].legend(ncol=2)
    axes_grid[2].grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_directory / "perforated_event_stage_history.png", dpi=180)
    plt.close(figure)
####


def _validate(
    frames: tuple[EventPlaneFrame, ...],
    initial_pressure: FloatArray,
    event_start_time: float,
    thresholds: EventValidationParameters,
) -> dict[str, bool | float | None]:
    initial_peak = float(np.max(initial_pressure))
    pressure_rise = max(frame.maximum_pressure for frame in frames) - initial_peak
    phase_peak = max(frame.maximum_phase_fraction for frame in frames)
    speed_peak = max(frame.maximum_speed for frame in frames)
    activation_indices = [
        index for index, frame in enumerate(frames) if frame.time >= event_start_time
    ]
    phase_indices = [
        index
        for index, frame in enumerate(frames)
        if frame.maximum_phase_fraction >= thresholds.minimum_phase_fraction
    ]
    pressure_indices = [
        index
        for index, frame in enumerate(frames)
        if frame.maximum_pressure - initial_peak >= max(0.05 * pressure_rise, 1.0e-6)
    ]
    event_activation_time = (
        frames[activation_indices[0]].time if activation_indices else None
    )
    pressure_time = frames[pressure_indices[0]].time if pressure_indices else None
    phase_time = frames[phase_indices[0]].time if phase_indices else None
    finite = all(
        np.all(np.isfinite(values))
        for frame in frames
        for values in (
            frame.density,
            frame.pressure,
            frame.temperature,
            frame.activity,
            frame.phase_fraction,
            frame.speed,
        )
    )
    bounded = all(
        np.all((frame.activity >= 0.0) & (frame.activity <= 1.0))
        and np.all((frame.phase_fraction >= 0.0) & (frame.phase_fraction <= 1.0))
        for frame in frames
    )
    causal = (
        event_activation_time is not None
        and pressure_time is not None
        and phase_time is not None
        and event_activation_time <= pressure_time <= phase_time
    )
    return {
        "finite_fields": finite,
        "bounded_source_and_phase": bounded,
        "localized_event_enabled": event_activation_time is not None,
        "pressure_wave_forms": pressure_rise > thresholds.minimum_pressure_rise,
        "phase_transition_occurs": phase_peak > thresholds.minimum_phase_fraction,
        "material_motion_forms": speed_peak > thresholds.minimum_speed,
        "causal_event_pressure_phase_order": (
            causal if thresholds.require_causal_order else True
        ),
        "event_activation_time": event_activation_time,
        "pressure_response_time": pressure_time,
        "phase_onset_time": phase_time,
        "maximum_pressure_rise": pressure_rise,
        "maximum_phase_fraction": phase_peak,
        "maximum_speed": speed_peak,
    }
####


def run_demo(
    output_directory: Path,
    requested_backend: BackendName,
    resolution: int = 48,
    event_final_time: float = 0.16,
    event_start_time: float = 0.035,
    frames: int = 101,
    fps: int = 16,
    event_center: tuple[float, float, float] = (-0.50, 0.52, -0.30),
    event_width: float = 0.14,
    parameters: PerforatedBlockEventParameters | None = None,
) -> None:
    parameters = parameters or PerforatedBlockEventParameters(
        precursor=PerforatedBlockParameters(
            resolution=resolution,
            backend=requested_backend,
        ),
        event=EventFootprintParameters(
            center=event_center,
            width=event_width,
            activation_time=event_start_time,
            final_time=event_final_time,
        ),
        presentation=PresentationParameters(frames=frames, fps=fps),
    )
    resolution = parameters.precursor.resolution
    requested_backend = parameters.precursor.backend
    event_final_time = parameters.event.final_time
    event_start_time = parameters.event.activation_time
    event_center = parameters.event.center
    event_width = parameters.event.width
    frames = parameters.presentation.frames
    fps = parameters.presentation.fps
    if resolution < 24:
        raise ValueError("resolution must be at least 24")
    ####
    if not 0.0 <= event_start_time < event_final_time:
        raise ValueError("event start time must lie inside the Euler stage")
    ####
    if frames < 2 or fps < 1:
        raise ValueError("frames must be at least two and fps must be positive")
    ####
    output_directory.mkdir(parents=True, exist_ok=True)

    precursor = run_radiant_wave(
        perforated_block_regulation_config(parameters=parameters.precursor),
        snapshot_count=81,
    )
    permission = _event_permission(
        precursor,
        event_center,
        event_width,
        parameters.coupling,
    )
    if float(np.max(permission)) <= 0.0:
        raise RuntimeError("event footprint does not overlap the active medium")
    ####
    z_index = _event_plane_index(permission)
    coordinate = precursor.coordinates[0]
    heat_offset = parameters.initial_state.heat_pressure_offset * _normalized(
        precursor.heat
    )
    initial_pressure = parameters.initial_state.pressure + heat_offset
    _save_handoff(
        coordinate,
        float(precursor.coordinates[2][z_index]),
        precursor,
        permission,
        initial_pressure,
        z_index,
        output_directory,
    )

    backend = get_array_backend(requested_backend)
    config = phase_impulse_config(parameters.phase)
    source_permission = backend.asarray(permission)
    density = backend.xp.full(
        (resolution, resolution, resolution),
        parameters.initial_state.density,
        dtype=np.float64,
    )
    velocity = backend.xp.zeros(
        (3, resolution, resolution, resolution), dtype=np.float64
    )
    pressure = backend.asarray(initial_pressure)
    state = primitive_to_phase_conservative(
        density,
        velocity,
        pressure,
        parameters.initial_state.activity_seed_fraction * source_permission,
        backend.xp.zeros_like(source_permission),
        config,
        backend,
    )
    activation = LinearRamp(event_start_time, event_start_time)
    spacing = (2.0 * parameters.precursor.half_extent / resolution,) * 3
    target_times = capture_times(event_final_time, frames)
    captured = [_capture_plane_frame(0.0, state, config, backend, z_index)]
    next_target = 1
    time = 0.0
    steps = 0
    while time < event_final_time:
        timestep = min(
            stable_phase_timestep(state, spacing, parameters.numerics.cfl, config, backend),
            parameters.numerics.maximum_timestep,
            event_final_time - time,
        )
        if time < event_start_time:
            timestep = min(timestep, event_start_time - time)
        ####
        source = source_permission * activation.fraction_at(time + timestep)
        state = advance_impulsive_phase_euler_split(
            state,
            source,
            timestep,
            spacing,
            config,
            backend,
        )
        time += timestep
        steps += 1
        while next_target < frames and time >= target_times[next_target] - 1.0e-14:
            captured.append(_capture_plane_frame(time, state, config, backend, z_index))
            next_target += 1
        ####
    ####
    backend.synchronize()
    frame_tuple = tuple(captured)
    validation = _validate(
        frame_tuple,
        initial_pressure,
        event_start_time,
        parameters.validation,
    )
    if not all(value for value in validation.values() if isinstance(value, bool)):
        raise RuntimeError(f"3D perforated event validation failed: {validation}")
    ####
    final = frame_tuple[-1]
    _save_final_fields(
        coordinate,
        float(precursor.coordinates[2][z_index]),
        permission,
        initial_pressure,
        final,
        z_index,
        output_directory,
    )
    _save_animation(
        coordinate,
        frame_tuple,
        permission,
        initial_pressure,
        z_index,
        output_directory,
        fps,
    )
    _save_stage_history(precursor, frame_tuple, event_start_time, output_directory)
    final_density, final_velocity, final_pressure, final_activity, final_phase = (
        phase_conservative_to_primitive(state, config, backend)
    )
    np.savez_compressed(
        output_directory / "perforated_event_state.npz",
        coordinate=coordinate,
        event_center=np.array(event_center),
        event_permission=permission,
        initial_pressure=initial_pressure,
        final_density=backend.to_numpy(final_density),
        final_velocity=backend.to_numpy(final_velocity),
        final_pressure=backend.to_numpy(final_pressure),
        final_activity=backend.to_numpy(final_activity),
        final_phase_fraction=backend.to_numpy(final_phase),
        event_plane_z_index=np.array(z_index),
        frame_time=np.array([frame.time for frame in frame_tuple]),
        frame_pressure=np.stack([frame.pressure for frame in frame_tuple]),
        frame_temperature=np.stack([frame.temperature for frame in frame_tuple]),
        frame_activity=np.stack([frame.activity for frame in frame_tuple]),
        frame_phase_fraction=np.stack([frame.phase_fraction for frame in frame_tuple]),
        frame_speed=np.stack([frame.speed for frame in frame_tuple]),
    )
    summary = {
        "requested_backend": requested_backend,
        "resolved_backend": backend.name,
        "resolution": resolution,
        "precursor_final_time": precursor.time,
        "event_final_time": time,
        "event_start_time": event_start_time,
        "event_center": event_center,
        "event_width": event_width,
        "event_steps": steps,
        "frames": len(frame_tuple),
        "thermal_model": asdict(config),
        "experiment_parameters": asdict(parameters),
        "validation": validation,
        "model_note": (
            "The settled scalar-wave fields and material IDs form a normalized "
            "3D permission and initial thermal-offset handoff. The Euler stage "
            "uses a homogeneous normalized continuum and independently computes "
            "thermodynamic pressure, temperature, velocity, and phase; this is "
            "not a calibrated shared material law."
        ),
    }
    write_summary(output_directory / "perforated_event_summary.json", summary)
####


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a regulated 3D perforated block followed by a finite 3D event"
    )
    parser.add_argument("--backend", choices=("auto", "numpy", "cupy"), default="auto")
    parser.add_argument("--resolution", type=int, default=48)
    parser.add_argument("--final-time", type=float, default=0.16)
    parser.add_argument("--event-time", type=float, default=0.035)
    parser.add_argument(
        "--event-center", type=float, nargs=3, default=(-0.50, 0.52, -0.30)
    )
    parser.add_argument("--event-width", type=float, default=0.14)
    parser.add_argument("--frames", type=int, default=101)
    parser.add_argument("--fps", type=int, default=16)
    parser.add_argument(
        "--parameters",
        type=Path,
        help="complete JSON or optional YAML experiment document",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/converging-flow/perforated-block-3d-event"),
    )
    arguments = parser.parse_args()
    if arguments.parameters:
        run_demo(arguments.output, cast(BackendName, arguments.backend), parameters=(
            perforated_block_event_parameters_from_file(arguments.parameters)
        ))
    else:
        run_demo(
            arguments.output,
            cast(BackendName, arguments.backend),
            arguments.resolution,
            arguments.final_time,
            arguments.event_time,
            arguments.frames,
            arguments.fps,
            cast(tuple[float, float, float], tuple(arguments.event_center)),
            arguments.event_width,
        )
    ####
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
