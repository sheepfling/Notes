from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from converging_flow.euler import FloatArray, conservative_to_primitive
from converging_flow.experiment import (
    RadialProfile,
    SimulationResult,
    radial_profile_data,
)


def _save_line(
    x: FloatArray,
    y: FloatArray,
    xlabel: str,
    ylabel: str,
    title: str,
    path: Path,
    *,
    labels: tuple[str, ...] = (),
) -> None:
    figure, axes = plt.subplots(figsize=(8, 5))
    if y.ndim == 1:
        axes.plot(x, y)
    else:
        for index, row in enumerate(y):
            label = labels[index] if index < len(labels) else None
            axes.plot(x, row, label=label)
        ####
    ####
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    axes.set_title(title)
    axes.grid(True, alpha=0.25)
    if labels:
        axes.legend()
    ####
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)
####


def _save_image(
    image: FloatArray,
    extent: tuple[float, float, float, float],
    label: str,
    title: str,
    path: Path,
    *,
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    figure, axes = plt.subplots(figsize=(7, 6))
    rendered = axes.imshow(
        image.T,
        origin="lower",
        extent=extent,
        aspect="equal",
        vmin=vmin,
        vmax=vmax,
    )
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_title(title)
    figure.colorbar(rendered, ax=axes, label=label)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)
####


def _primitive_observables(
    result: SimulationResult,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]:
    density, velocity, pressure = conservative_to_primitive(
        result.state,
        result.config.gamma,
        result.config.density_floor,
        result.config.pressure_floor,
    )
    speed = np.sqrt(np.sum(velocity * velocity, axis=0))
    sound_speed = np.sqrt(result.config.gamma * pressure / density)
    mach = speed / sound_speed
    return density, velocity, pressure, speed, mach
####


def _central_slice(values: FloatArray, dimensions: int) -> FloatArray:
    if dimensions < 3:
        return values
    ####
    return values[:, :, values.shape[2] // 2]
####


def _radial_velocity_field(
    result: SimulationResult,
    velocity: FloatArray,
) -> FloatArray:
    mesh = np.meshgrid(*result.coordinates, indexing="ij", sparse=True)
    radius_squared = np.zeros(result.config.resolution, dtype=np.float64)
    for coordinate in mesh:
        radius_squared += coordinate * coordinate
    ####
    radius = np.sqrt(radius_squared)
    safe_radius = np.where(radius > 0.0, radius, 1.0)
    radial_velocity = np.zeros(result.config.resolution, dtype=np.float64)
    for axis, coordinate in enumerate(mesh):
        radial_velocity += velocity[axis] * coordinate / safe_radius
    ####
    return np.where(radius > 0.0, radial_velocity, 0.0)
####


def _save_quiver(
    result: SimulationResult,
    density: FloatArray,
    velocity: FloatArray,
    output_path: Path,
) -> None:
    if result.config.dimensions == 1:
        return
    ####

    if result.config.dimensions == 2:
        density_slice = density
        velocity_x = velocity[0]
        velocity_y = velocity[1]
    else:
        middle = result.config.resolution[2] // 2
        density_slice = density[:, :, middle]
        velocity_x = velocity[0, :, :, middle]
        velocity_y = velocity[1, :, :, middle]
    ####

    x = result.coordinates[0]
    y = result.coordinates[1]
    stride = max(1, min(len(x), len(y)) // 24)
    sampled_x = x[::stride]
    sampled_y = y[::stride]
    mesh_x, mesh_y = np.meshgrid(sampled_x, sampled_y, indexing="ij")

    extent = (
        -result.config.half_extent,
        result.config.half_extent,
        -result.config.half_extent,
        result.config.half_extent,
    )
    figure, axes = plt.subplots(figsize=(7, 6))
    rendered = axes.imshow(
        (density_slice / result.config.ambient_density).T,
        origin="lower",
        extent=extent,
        aspect="equal",
    )
    axes.quiver(
        mesh_x,
        mesh_y,
        velocity_x[::stride, ::stride],
        velocity_y[::stride, ::stride],
        angles="xy",
        scale_units="xy",
    )
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_title(
        f"{result.config.dimensions}D density ratio with velocity vectors, "
        f"t = {result.time:.4f}"
    )
    figure.colorbar(rendered, ax=axes, label="density / ambient density")
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)
####


def _save_orthogonal_slices(
    result: SimulationResult,
    values: FloatArray,
    label: str,
    output_directory: Path,
) -> None:
    if result.config.dimensions != 3:
        return
    ####

    midpoint = tuple(size // 2 for size in result.config.resolution)
    extent = (
        -result.config.half_extent,
        result.config.half_extent,
        -result.config.half_extent,
        result.config.half_extent,
    )
    slices = {
        "xy": values[:, :, midpoint[2]],
        "xz": values[:, midpoint[1], :],
        "yz": values[midpoint[0], :, :],
    }
    for plane, image in slices.items():
        _save_image(
            image,
            extent,
            label,
            f"3D {plane.upper()} central slice: {label}, t = {result.time:.4f}",
            output_directory / f"{label}_{plane}.png",
        )
    ####
####


def _save_density_projections(
    result: SimulationResult,
    density: FloatArray,
    output_directory: Path,
) -> None:
    if result.config.dimensions != 3:
        return
    ####

    extent = (
        -result.config.half_extent,
        result.config.half_extent,
        -result.config.half_extent,
        result.config.half_extent,
    )
    for axis, name in enumerate(("x", "y", "z")):
        projection = np.mean(density, axis=axis) / result.config.ambient_density
        _save_image(
            projection,
            extent,
            "line-of-sight mean density / ambient density",
            f"3D mean-density projection along {name}, t = {result.time:.4f}",
            output_directory / f"density_projection_{name}.png",
        )
    ####
####


def _save_radial_plots(
    profile: RadialProfile,
    result: SimulationResult,
    output_directory: Path,
) -> None:
    time_text = f"t = {result.time:.4f}"
    density_relative_scatter = profile.density_standard_deviation / np.maximum(
        np.abs(profile.density),
        result.config.density_floor,
    )
    pressure_relative_scatter = profile.pressure_standard_deviation / np.maximum(
        np.abs(profile.pressure),
        result.config.pressure_floor,
    )
    items = (
        (profile.density, "mean density", "radial_density.png"),
        (profile.pressure, "mean pressure", "radial_pressure.png"),
        (profile.speed, "mean speed", "radial_speed.png"),
        (
            profile.radial_velocity,
            "mean radial velocity (negative is inward)",
            "radial_velocity_profile.png",
        ),
        (profile.mach, "mean Mach number", "radial_mach.png"),
        (
            density_relative_scatter,
            "density shell standard deviation / shell mean",
            "density_symmetry_error.png",
        ),
        (
            pressure_relative_scatter,
            "pressure shell standard deviation / shell mean",
            "pressure_symmetry_error.png",
        ),
    )
    for values, ylabel, filename in items:
        _save_line(
            profile.radius,
            values,
            "radius",
            ylabel,
            f"{result.config.dimensions}D radial profile, {time_text}",
            output_directory / filename,
        )
    ####
####


def save_plots(result: SimulationResult, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    density, velocity, pressure, speed, mach = _primitive_observables(result)
    radial_velocity = _radial_velocity_field(result, velocity)
    time_text = f"t = {result.time:.4f}"

    fields = (
        (density, "density", "density.png"),
        (pressure, "pressure", "pressure.png"),
        (speed, "speed", "speed.png"),
        (
            radial_velocity,
            "radial velocity (negative is inward)",
            "radial_velocity.png",
        ),
        (mach, "Mach number", "mach.png"),
    )

    if result.config.dimensions == 1:
        x = result.coordinates[0]
        for values, label, filename in fields:
            _save_line(
                x,
                values,
                "x",
                label,
                f"1D {label}, {time_text}",
                output_directory / filename,
            )
        ####
    else:
        extent = (
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        )
        for values, label, filename in fields:
            _save_image(
                _central_slice(values, result.config.dimensions),
                extent,
                label,
                f"{result.config.dimensions}D central slice: {label}, {time_text}",
                output_directory / filename,
            )
        ####
        _save_quiver(result, density, velocity, output_directory / "flow_vectors.png")
    ####

    profile = radial_profile_data(result)
    _save_radial_plots(profile, result, output_directory)
    _save_orthogonal_slices(result, density, "density", output_directory)
    _save_orthogonal_slices(result, pressure, "pressure", output_directory)
    _save_density_projections(result, density, output_directory)
####


def _profile_quantity(profile: RadialProfile, quantity: str) -> FloatArray:
    if quantity == "density":
        return profile.density
    ####
    if quantity == "pressure":
        return profile.pressure
    ####
    if quantity == "speed":
        return profile.speed
    ####
    if quantity == "radial_velocity":
        return profile.radial_velocity
    ####
    if quantity == "mach":
        return profile.mach
    ####
    raise ValueError(f"unsupported radial-profile quantity: {quantity}")
####


def _save_field_animation(
    result: SimulationResult,
    quantity: str,
    label: str,
    path: Path,
    fps: int,
) -> None:
    frames = result.frames
    if not frames:
        return
    ####

    values = [getattr(frame, f"{quantity}_field") for frame in frames]
    minimum = min(float(np.min(value)) for value in values)
    maximum = max(float(np.max(value)) for value in values)

    if result.config.dimensions == 1:
        figure, axes = plt.subplots(figsize=(8, 5))
        line, = axes.plot(result.coordinates[0], values[0])
        axes.set_xlim(-result.config.half_extent, result.config.half_extent)
        padding = 0.05 * max(maximum - minimum, 1.0)
        axes.set_ylim(minimum - padding, maximum + padding)
        axes.set_xlabel("x")
        axes.set_ylabel(label)
        axes.grid(True, alpha=0.25)

        def update(index: int) -> tuple[object, ...]:
            line.set_ydata(values[index])
            axes.set_title(
                f"1D {label} evolution, t = {frames[index].time:.4f}"
            )
            return (line,)
        ####
    else:
        extent = (
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        )
        figure, axes = plt.subplots(figsize=(7, 6))
        image = axes.imshow(
            values[0].T,
            origin="lower",
            extent=extent,
            aspect="equal",
            vmin=minimum,
            vmax=maximum,
        )
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        figure.colorbar(image, ax=axes, label=label)

        def update(index: int) -> tuple[object, ...]:
            image.set_data(values[index].T)
            axes.set_title(
                f"{result.config.dimensions}D central-slice {label}, "
                f"t = {frames[index].time:.4f}"
            )
            return (image,)
        ####
    ####

    animation = FuncAnimation(
        figure,
        update,
        frames=len(frames),
        interval=1000 / fps,
        blit=False,
    )
    figure.tight_layout()
    animation.save(path, writer=PillowWriter(fps=fps), dpi=120)
    plt.close(figure)
####


def _save_radial_animation(
    result: SimulationResult,
    quantity: str,
    label: str,
    path: Path,
    fps: int,
) -> None:
    frames = result.frames
    if not frames:
        return
    ####

    values = [_profile_quantity(frame.radial_profile, quantity) for frame in frames]
    minimum = min(float(np.min(value)) for value in values)
    maximum = max(float(np.max(value)) for value in values)
    radius = frames[0].radial_profile.radius

    figure, axes = plt.subplots(figsize=(8, 5))
    line, = axes.plot(radius, values[0])
    padding = 0.05 * max(maximum - minimum, 1.0)
    axes.set_xlim(float(radius[0]), float(radius[-1]))
    axes.set_ylim(minimum - padding, maximum + padding)
    axes.set_xlabel("radius")
    axes.set_ylabel(label)
    axes.grid(True, alpha=0.25)

    def update(index: int) -> tuple[object, ...]:
        line.set_ydata(values[index])
        axes.set_title(
            f"{result.config.dimensions}D radial {label}, "
            f"t = {frames[index].time:.4f}"
        )
        return (line,)
    ####

    animation = FuncAnimation(
        figure,
        update,
        frames=len(frames),
        interval=1000 / fps,
        blit=False,
    )
    figure.tight_layout()
    animation.save(path, writer=PillowWriter(fps=fps), dpi=120)
    plt.close(figure)
####


def save_animations(
    result: SimulationResult,
    output_directory: Path,
    fps: int = 12,
) -> None:
    if not result.frames:
        raise ValueError("result has no visualization frames")
    ####
    if fps < 1:
        raise ValueError("fps must be positive")
    ####

    output_directory.mkdir(parents=True, exist_ok=True)
    _save_field_animation(
        result,
        "density",
        "density",
        output_directory / "density_evolution.gif",
        fps,
    )
    _save_field_animation(
        result,
        "radial_velocity",
        "radial velocity (negative is inward)",
        output_directory / "radial_velocity_evolution.gif",
        fps,
    )
    _save_radial_animation(
        result,
        "density",
        "density",
        output_directory / "radial_density_evolution.gif",
        fps,
    )
####


def save_comparison(
    results: Iterable[SimulationResult],
    output_directory: Path,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    result_list = list(results)
    ambient_sound_speeds = {
        result.config.dimensions: np.sqrt(
            result.config.gamma
            * result.config.ambient_pressure
            / result.config.ambient_density
        )
        for result in result_list
    }
    quantities = (
        (
            "density",
            "density / ambient density",
            "comparison_density.png",
            lambda result, profile: profile.density / result.config.ambient_density,
        ),
        (
            "pressure",
            "pressure / ambient pressure",
            "comparison_pressure.png",
            lambda result, profile: profile.pressure / result.config.ambient_pressure,
        ),
        (
            "radial_velocity",
            "radial velocity / ambient sound speed",
            "comparison_radial_velocity.png",
            lambda result, profile: (
                profile.radial_velocity
                / ambient_sound_speeds[result.config.dimensions]
            ),
        ),
        (
            "mach",
            "mean Mach number",
            "comparison_mach.png",
            lambda _result, profile: profile.mach,
        ),
        (
            "density_symmetry_error",
            "density shell standard deviation / shell mean",
            "comparison_density_symmetry_error.png",
            lambda result, profile: (
                profile.density_standard_deviation
                / np.maximum(np.abs(profile.density), result.config.density_floor)
            ),
        ),
    )

    for quantity, ylabel, filename, transform in quantities:
        figure, axes = plt.subplots(figsize=(8, 5))
        for result in result_list:
            profile = radial_profile_data(result)
            axes.plot(
                profile.radius / result.config.half_extent,
                transform(result, profile),
                label=f"{result.config.dimensions}D",
            )
        ####
        axes.set_xlabel("radius / domain half-extent")
        axes.set_ylabel(ylabel)
        axes.set_title(f"Cross-dimensional normalized {quantity.replace('_', ' ')}")
        axes.grid(True, alpha=0.25)
        axes.legend()
        figure.tight_layout()
        figure.savefig(output_directory / filename, dpi=180)
        plt.close(figure)
    ####

    if all(result.frames for result in result_list):
        _save_history_comparison(result_list, output_directory)
    ####
####


def _save_history_comparison(
    results: list[SimulationResult],
    output_directory: Path,
) -> None:
    metrics = (
        (
            "peak_density",
            "peak radial-mean density / ambient density",
            "history_peak_density.png",
        ),
        (
            "peak_pressure",
            "peak radial-mean pressure / ambient pressure",
            "history_peak_pressure.png",
        ),
        ("peak_mach", "peak radial-mean Mach number", "history_peak_mach.png"),
        (
            "peak_radius",
            "radius of peak radial-mean density / half-extent",
            "history_peak_radius.png",
        ),
        (
            "density_symmetry_error",
            "maximum density shell standard deviation / shell mean",
            "history_density_symmetry_error.png",
        ),
    )

    for metric, ylabel, filename in metrics:
        figure, axes = plt.subplots(figsize=(8, 5))
        for result in results:
            time = np.array([frame.time for frame in result.frames]) / result.config.final_time
            if metric == "peak_density":
                values = np.array(
                    [
                        np.max(frame.radial_profile.density)
                        / result.config.ambient_density
                        for frame in result.frames
                    ]
                )
            elif metric == "peak_pressure":
                values = np.array(
                    [
                        np.max(frame.radial_profile.pressure)
                        / result.config.ambient_pressure
                        for frame in result.frames
                    ]
                )
            elif metric == "peak_mach":
                values = np.array(
                    [np.max(frame.radial_profile.mach) for frame in result.frames]
                )
            elif metric == "peak_radius":
                values = np.array(
                    [
                        frame.radial_profile.radius[
                            int(np.argmax(frame.radial_profile.density))
                        ]
                        / result.config.half_extent
                        for frame in result.frames
                    ]
                )
            else:
                values = np.array(
                    [
                        np.max(
                            frame.radial_profile.density_standard_deviation
                            / np.maximum(
                                np.abs(frame.radial_profile.density),
                                result.config.density_floor,
                            )
                        )
                        for frame in result.frames
                    ]
                )
            ####
            axes.plot(time, values, label=f"{result.config.dimensions}D")
        ####
        axes.set_xlabel("time / final time")
        axes.set_ylabel(ylabel)
        axes.set_title(ylabel.capitalize())
        axes.grid(True, alpha=0.25)
        axes.legend()
        figure.tight_layout()
        figure.savefig(output_directory / filename, dpi=180)
        plt.close(figure)
    ####
####
