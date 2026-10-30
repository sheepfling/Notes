from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from converging_flow.reaction_diffusion import FloatArray, ReactionResult


def _save_line(
    x: FloatArray,
    values: tuple[FloatArray, ...],
    labels: tuple[str, ...],
    ylabel: str,
    title: str,
    path: Path,
) -> None:
    figure, axes = plt.subplots(figsize=(8, 5))
    for value, label in zip(values, labels, strict=True):
        axes.plot(x, value, label=label)
    ####
    axes.set_xlabel("position")
    axes.set_ylabel(ylabel)
    axes.set_title(title)
    axes.grid(True, alpha=0.25)
    if len(values) > 1:
        axes.legend()
    ####
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)
####


def _save_image(
    values: FloatArray,
    extent: tuple[float, float, float, float],
    label: str,
    title: str,
    path: Path,
    *,
    symmetric: bool = False,
) -> None:
    figure, axes = plt.subplots(figsize=(7, 6))
    minimum: float | None = None
    maximum: float | None = None
    if symmetric:
        bound = float(np.max(np.abs(values)))
        minimum = -bound
        maximum = bound
    ####
    image = axes.imshow(
        values.T,
        origin="lower",
        extent=extent,
        aspect="equal",
        vmin=minimum,
        vmax=maximum,
    )
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_title(title)
    figure.colorbar(image, ax=axes, label=label)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)
####


def _central_slice(values: FloatArray) -> FloatArray:
    if values.ndim < 3:
        return values
    ####
    return values[:, :, values.shape[2] // 2]
####


def _radial_profile(
    result: ReactionResult,
    values: FloatArray,
    bins: int = 128,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    mesh = np.meshgrid(*result.coordinates, indexing="ij", sparse=True)
    radius_squared = np.zeros(result.config.resolution, dtype=np.float64)
    for coordinate in mesh:
        radius_squared += coordinate * coordinate
    ####
    radius = np.sqrt(radius_squared)
    edges = np.linspace(0.0, result.config.half_extent, bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    inside = radius.ravel() <= result.config.half_extent
    indices = np.clip(
        np.digitize(radius.ravel()[inside], edges) - 1,
        0,
        bins - 1,
    )
    counts = np.bincount(indices, minlength=bins).astype(np.float64)
    sums = np.bincount(
        indices,
        weights=values.ravel()[inside],
        minlength=bins,
    )
    square_sums = np.bincount(
        indices,
        weights=values.ravel()[inside] ** 2,
        minlength=bins,
    )
    populated = counts > 0.0
    mean = sums[populated] / counts[populated]
    variance = square_sums[populated] / counts[populated] - mean * mean
    return (
        centers,
        np.interp(centers, centers[populated], mean),
        np.interp(
            centers,
            centers[populated],
            np.sqrt(np.maximum(variance, 0.0)),
        ),
    )
####


def _save_orthogonal_slices(
    result: ReactionResult,
    values: FloatArray,
    name: str,
    label: str,
    output_directory: Path,
    *,
    symmetric: bool = False,
) -> None:
    if result.config.dimensions != 3:
        return
    ####
    middle = tuple(size // 2 for size in result.config.resolution)
    slices = {
        "xy": values[:, :, middle[2]],
        "xz": values[:, middle[1], :],
        "yz": values[middle[0], :, :],
    }
    extent = (
        -result.config.half_extent,
        result.config.half_extent,
        -result.config.half_extent,
        result.config.half_extent,
    )
    for plane, image in slices.items():
        _save_image(
            image,
            extent,
            label,
            f"3D {plane.upper()} slice: {label}, t = {result.time:.3f}",
            output_directory / f"{name}_{plane}.png",
            symmetric=symmetric,
        )
    ####
####


def _save_projections(result: ReactionResult, output_directory: Path) -> None:
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
        _save_image(
            np.mean(result.activity, axis=axis),
            extent,
            "mean activity",
            f"3D activity projection along {name}, t = {result.time:.3f}",
            output_directory / f"activity_projection_{name}.png",
        )
    ####
####


def save_reaction_plots(result: ReactionResult, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    time_text = f"t = {result.time:.3f}"
    fields = (
        (result.activity, "activity", "activity", False),
        (result.heat, "heat", "heat", False),
        (result.wave, "wave displacement", "wave", True),
        (result.catalyst, "catalyst fraction", "catalyst", False),
        (result.quencher, "quencher fraction", "quencher", False),
    )

    if result.config.dimensions == 1:
        x = result.coordinates[0]
        for values, label, filename, _symmetric in fields:
            _save_line(
                x,
                (values,),
                (label,),
                label,
                f"1D {label}, {time_text}",
                output_directory / f"{filename}.png",
            )
        ####
        _save_line(
            x,
            (result.activity, result.heat),
            ("activity", "heat"),
            "normalized field",
            f"1D activity and heat, {time_text}",
            output_directory / "activity_heat_overlay.png",
        )
    else:
        extent = (
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        )
        for values, label, filename, symmetric in fields:
            _save_image(
                _central_slice(values),
                extent,
                label,
                f"{result.config.dimensions}D central slice: {label}, {time_text}",
                output_directory / f"{filename}.png",
                symmetric=symmetric,
            )
        ####
    ####

    for values, label, filename, _symmetric in fields[:3]:
        radius, mean, standard_deviation = _radial_profile(result, values)
        _save_line(
            radius,
            (mean,),
            (label,),
            f"shell-mean {label}",
            f"{result.config.dimensions}D radial {label}, {time_text}",
            output_directory / f"radial_{filename}.png",
        )
        relative_scatter = standard_deviation / np.maximum(np.abs(mean), 1.0e-12)
        _save_line(
            radius,
            (relative_scatter,),
            ("relative shell scatter",),
            "shell standard deviation / |shell mean|",
            f"{result.config.dimensions}D {label} symmetry error, {time_text}",
            output_directory / f"{filename}_symmetry_error.png",
        )
    ####

    _save_orthogonal_slices(
        result,
        result.activity,
        "activity",
        "activity",
        output_directory,
    )
    _save_orthogonal_slices(
        result,
        result.heat,
        "heat",
        "heat",
        output_directory,
    )
    _save_orthogonal_slices(
        result,
        result.wave,
        "wave",
        "wave displacement",
        output_directory,
        symmetric=True,
    )
    _save_projections(result, output_directory)
####


def _save_animation(
    result: ReactionResult,
    field_name: str,
    label: str,
    output_path: Path,
    fps: int,
    *,
    symmetric: bool = False,
) -> None:
    if not result.frames:
        return
    ####
    values = [getattr(frame, field_name) for frame in result.frames]
    minimum = min(float(np.min(value)) for value in values)
    maximum = max(float(np.max(value)) for value in values)
    if symmetric:
        bound = max(abs(minimum), abs(maximum))
        minimum = -bound
        maximum = bound
    ####

    if result.config.dimensions == 1:
        figure, axes = plt.subplots(figsize=(8, 5))
        line, = axes.plot(result.coordinates[0], values[0])
        padding = 0.05 * max(maximum - minimum, 1.0)
        axes.set_xlim(-result.config.half_extent, result.config.half_extent)
        axes.set_ylim(minimum - padding, maximum + padding)
        axes.set_xlabel("position")
        axes.set_ylabel(label)
        axes.grid(True, alpha=0.25)

        def update(index: int) -> tuple[object, ...]:
            line.set_ydata(values[index])
            axes.set_title(
                f"1D {label} evolution, t = {result.frames[index].time:.3f}"
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
                f"t = {result.frames[index].time:.3f}"
            )
            return (image,)
        ####
    ####

    animation = FuncAnimation(
        figure,
        update,
        frames=len(result.frames),
        interval=1000 / fps,
        blit=False,
    )
    figure.tight_layout()
    animation.save(output_path, writer=PillowWriter(fps=fps), dpi=120)
    plt.close(figure)
####


def save_reaction_animations(
    result: ReactionResult,
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
    _save_animation(
        result,
        "activity",
        "activity",
        output_directory / "activity_evolution.gif",
        fps,
    )
    _save_animation(
        result,
        "heat",
        "heat",
        output_directory / "heat_evolution.gif",
        fps,
    )
    _save_animation(
        result,
        "wave",
        "wave displacement",
        output_directory / "wave_evolution.gif",
        fps,
        symmetric=True,
    )
####


def save_reaction_comparison(
    results: Iterable[ReactionResult],
    output_directory: Path,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    result_list = list(results)
    quantities = (
        ("activity", "shell-mean activity", "comparison_activity.png"),
        ("heat", "shell-mean heat", "comparison_heat.png"),
        ("wave", "shell-mean wave displacement", "comparison_wave.png"),
    )
    for attribute, ylabel, filename in quantities:
        figure, axes = plt.subplots(figsize=(8, 5))
        for result in result_list:
            radius, mean, _standard_deviation = _radial_profile(
                result,
                getattr(result, attribute),
            )
            axes.plot(
                radius / result.config.half_extent,
                mean,
                label=f"{result.config.dimensions}D",
            )
        ####
        axes.set_xlabel("radius / domain half-extent")
        axes.set_ylabel(ylabel)
        axes.set_title(f"Cross-dimensional {ylabel}")
        axes.grid(True, alpha=0.25)
        axes.legend()
        figure.tight_layout()
        figure.savefig(output_directory / filename, dpi=180)
        plt.close(figure)
    ####

    if all(result.frames for result in result_list):
        metrics = (
            ("maximum_activity", "maximum activity", "history_max_activity.png"),
            ("mean_activity", "mean displayed activity", "history_mean_activity.png"),
            ("maximum_heat", "maximum heat", "history_max_heat.png"),
            ("wave_rms", "wave RMS", "history_wave_rms.png"),
        )
        for metric, ylabel, filename in metrics:
            figure, axes = plt.subplots(figsize=(8, 5))
            for result in result_list:
                normalized_time = np.array(
                    [frame.time for frame in result.frames]
                ) / result.config.final_time
                if metric == "maximum_activity":
                    values = np.array(
                        [np.max(frame.activity) for frame in result.frames]
                    )
                elif metric == "mean_activity":
                    values = np.array(
                        [np.mean(frame.activity) for frame in result.frames]
                    )
                elif metric == "maximum_heat":
                    values = np.array([np.max(frame.heat) for frame in result.frames])
                else:
                    values = np.array(
                        [np.sqrt(np.mean(frame.wave * frame.wave)) for frame in result.frames]
                    )
                ####
                axes.plot(
                    normalized_time,
                    values,
                    label=f"{result.config.dimensions}D",
                )
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
####
