from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import BoundaryNorm, ListedColormap

from converging_flow.radiant_wave import (
    FloatArray,
    RadiantWaveResult,
    wave_energy_components,
)

_MATERIAL_LABELS = ("reflector", "reactive medium", "loss rod", "open channel")
_MATERIAL_COLORS = ("#355c7d", "#f8b195", "#c06c84", "#6c5b7b")


def _central_slice(values: FloatArray) -> FloatArray:
    if values.ndim < 3:
        return values
    ####
    return values[:, :, values.shape[2] // 2]
####

def _material_visualization_slice(
    values: FloatArray,
    result: RadiantWaveResult,
) -> FloatArray:
    """Use a channel-aligned longitudinal slice when rods move along z."""
    if result.config.material_layout == "channel-block" and values.ndim == 3:
        target_y = 0.14 * result.config.half_extent
        y_index = int(np.argmin(np.abs(result.coordinates[1] - target_y)))
        return values[:, y_index, :]
    ####
    return _central_slice(values)
####




def _save_line(
    x: FloatArray,
    values: FloatArray,
    label: str,
    title: str,
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(figsize=(8, 5))
    axes.plot(x, values)
    axes.set_xlabel("position")
    axes.set_ylabel(label)
    axes.set_title(title)
    axes.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
####




def _save_image(
    values: FloatArray,
    extent: tuple[float, float, float, float],
    label: str,
    title: str,
    output_path: Path,
    *,
    symmetric: bool = False,
) -> None:
    minimum: float | None = None
    maximum: float | None = None
    if symmetric:
        bound = max(abs(float(np.min(values))), abs(float(np.max(values))))
        minimum = -bound
        maximum = bound
    ####

    figure, axes = plt.subplots(figsize=(7, 6))
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
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
####




def _save_material_map(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    labels = _MATERIAL_LABELS
    if result.config.dimensions == 1:
        figure, axes = plt.subplots(figsize=(8, 2.8))
        axes.step(
            result.coordinates[0],
            result.materials.material_id,
            where="mid",
        )
        axes.set_yticks(range(len(labels)), labels=labels)
        axes.set_xlabel("position")
        axes.set_title("Material regions")
        axes.grid(True, axis="x", alpha=0.25)
    else:
        extent = (
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        )
        figure, axes = plt.subplots(figsize=(7, 6))
        colormap = ListedColormap(_MATERIAL_COLORS)
        norm = BoundaryNorm((-0.5, 0.5, 1.5, 2.5, 3.5), colormap.N)
        image = axes.imshow(
            _material_visualization_slice(result.materials.material_id, result).T,
            origin="lower",
            extent=extent,
            aspect="equal",
            cmap=colormap,
            norm=norm,
        )
        axes.set_xlabel("x")
        axes.set_ylabel(
            "z" if result.config.material_layout == "channel-block" else "y"
        )
        axes.set_title("Material regions")
        colorbar = figure.colorbar(image, ax=axes, ticks=range(len(labels)))
        colorbar.ax.set_yticklabels(labels)
    ####
    figure.tight_layout()
    figure.savefig(output_directory / "materials.png", dpi=160)
    plt.close(figure)
####




def _save_channel_block_geometry(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    """Show both the 6×4 channel grid and its final axial rod depth."""
    if result.config.material_layout != "channel-block":
        return
    ####
    material_id = result.materials.material_id
    coordinates = result.coordinates
    upper_z = int(np.argmin(np.abs(coordinates[2] - 0.40 * result.config.half_extent)))
    lower_z = int(np.argmin(np.abs(coordinates[2] + 0.40 * result.config.half_extent)))
    target_y = 0.14 * result.config.half_extent
    y_index = int(np.argmin(np.abs(coordinates[1] - target_y)))
    extent = (
        -result.config.half_extent,
        result.config.half_extent,
        -result.config.half_extent,
        result.config.half_extent,
    )
    colormap = ListedColormap(_MATERIAL_COLORS)
    norm = BoundaryNorm((-0.5, 0.5, 1.5, 2.5, 3.5), colormap.N)
    figure, axes_with_colorbar = plt.subplots(
        1,
        4,
        figsize=(16, 5),
        gridspec_kw={"width_ratios": (1, 1, 1, 0.08), "wspace": 0.35},
        constrained_layout=True,
    )
    axes = axes_with_colorbar[:3]
    colorbar_axis = axes_with_colorbar[3]
    panels = (
        (
            material_id[:, :, lower_z],
            "Lower axial cross-section: open channels",
            "y",
        ),
        (
            material_id[:, :, upper_z],
            "Upper axial cross-section: inserted loss rods",
            "y",
        ),
        (
            material_id[:, y_index, :],
            "Longitudinal channel row: 50% insertion",
            "z",
        ),
    )
    image = None
    for axis, (values, title, vertical_label) in zip(axes, panels, strict=True):
        image = axis.imshow(
            values.T,
            origin="lower",
            extent=extent,
            aspect="equal",
            cmap=colormap,
            norm=norm,
        )
        axis.set_xlabel("x")
        axis.set_ylabel(vertical_label)
        axis.set_title(title)
    ####
    assert image is not None
    colorbar_axis.set_ylabel("material regime", rotation=270, labelpad=18)
    colorbar_axis.set_yticks([])
    colorbar = figure.colorbar(
        image,
        cax=colorbar_axis,
        ticks=range(len(_MATERIAL_LABELS)),
    )
    colorbar.ax.set_yticklabels(_MATERIAL_LABELS)
    figure.suptitle("Generic 6×4 channel block and time-ramped loss rods")
    figure.savefig(output_directory / "channel_block_geometry.png", dpi=180)
    plt.close(figure)
####




def _material_boundaries(result: RadiantWaveResult) -> tuple[float, float]:
    width = result.config.neutral_half_width
    return -width, width
####




def _shade_material_regions(
    axes: plt.Axes,
    result: RadiantWaveResult,
) -> None:
    if result.config.material_layout == "spherical-shell":
        shell_radius = 0.62 * result.config.half_extent
        axes.axvspan(
            -result.config.half_extent,
            -shell_radius,
            alpha=0.10,
            label="reflector shell",
        )
        axes.axvspan(
            -shell_radius,
            shell_radius,
            alpha=0.04,
            label="reactive interior",
        )
        axes.axvspan(
            shell_radius,
            result.config.half_extent,
            alpha=0.14,
            label="asymmetric absorbing cap",
        )
        return
    ####

    left, right = _material_boundaries(result)
    axes.axvspan(
        -result.config.half_extent,
        left,
        alpha=0.08,
        label="reflector",
    )
    axes.axvspan(left, right, alpha=0.04, label="neutral")
    axes.axvspan(
        right,
        result.config.half_extent,
        alpha=0.12,
        label="loss insert",
    )
####




def _plot_scalar_field(
    axes: plt.Axes,
    result: RadiantWaveResult,
    values: FloatArray,
    label: str,
    *,
    symmetric: bool = False,
) -> object:
    if result.config.dimensions == 1:
        (line,) = axes.plot(result.coordinates[0], values)
        _shade_material_regions(axes, result)
        axes.set_xlabel("position")
        axes.set_ylabel(label)
        axes.grid(True, alpha=0.25)
        return line
    ####

    displayed = _central_slice(values)
    minimum: float | None = None
    maximum: float | None = None
    if symmetric:
        bound = max(
            abs(float(np.min(displayed))),
            abs(float(np.max(displayed))),
        )
        minimum = -bound
        maximum = bound
    ####
    image = axes.imshow(
        displayed.T,
        origin="lower",
        extent=(
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        ),
        aspect="equal",
        vmin=minimum,
        vmax=maximum,
    )
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    return image
####




def _add_scalar_colorbar(
    figure: plt.Figure,
    axes: plt.Axes,
    artist: object,
    label: str,
    dimensions: int,
) -> None:
    if dimensions == 1:
        return
    ####
    figure.colorbar(artist, ax=axes, label=label)
####




def _derived_material_properties(
    result: RadiantWaveResult,
) -> tuple[tuple[FloatArray, str], ...]:
    materials = result.materials
    wave_speed = np.sqrt(materials.wave_stiffness / materials.wave_density)
    impedance = np.sqrt(materials.wave_density * materials.wave_stiffness)
    return (
        (materials.growth_rate, "autocatalytic growth rate"),
        (materials.loss_rate, "activity loss rate"),
        (materials.activity_diffusivity, "activity diffusivity"),
        (materials.thermal_conductivity, "thermal conductivity"),
        (materials.heat_capacity, "heat capacity"),
        (materials.heat_loss_rate, "heat loss rate"),
        (wave_speed, "wave speed"),
        (impedance, "wave impedance"),
        (materials.wave_damping, "wave damping"),
    )
####




def _save_material_property_atlas(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    figure, axes_grid = plt.subplots(3, 3, figsize=(14, 11))
    for axes, (values, label) in zip(
        axes_grid.flat,
        _derived_material_properties(result),
        strict=True,
    ):
        artist = _plot_scalar_field(axes, result, values, label)
        axes.set_title(label)
        _add_scalar_colorbar(
            figure,
            axes,
            artist,
            label,
            result.config.dimensions,
        )
    ####
    figure.suptitle("Material-property atlas: reaction, heat, and wave behavior")
    figure.tight_layout()
    figure.savefig(
        output_directory / "material_property_atlas.png",
        dpi=180,
    )
    plt.close(figure)
####




def _save_coupling_chain(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    fields = (
        (result.activity, "activity", False),
        (result.heat, "heat", False),
        (result.wave, "wave displacement", True),
        (result.wave_energy, "wave energy density", False),
        (result.wave_pressure, "wave-pressure proxy", False),
        (result.force_magnitude, "pressure-force magnitude", False),
    )
    figure, axes_grid = plt.subplots(2, 3, figsize=(15, 9))
    for axes, (values, label, symmetric) in zip(
        axes_grid.flat,
        fields,
        strict=True,
    ):
        artist = _plot_scalar_field(
            axes,
            result,
            values,
            label,
            symmetric=symmetric,
        )
        axes.set_title(label)
        _add_scalar_colorbar(
            figure,
            axes,
            artist,
            label,
            result.config.dimensions,
        )
    ####
    figure.suptitle("Coupling chain: activity → heat → wave → pressure diagnostic")
    figure.tight_layout()
    figure.savefig(output_directory / "coupling_chain.png", dpi=180)
    plt.close(figure)
####




def _save_wave_energy_partition(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    kinetic, strain = wave_energy_components(
        result.wave,
        result.wave_velocity,
        result.materials,
        result.config.spacing,
    )
    total = kinetic + strain
    visible_energy = max(float(np.max(total)) * 1.0e-3, 1.0e-15)
    kinetic_fraction = np.divide(
        kinetic,
        total,
        out=np.full_like(total, np.nan),
        where=total > visible_energy,
    )
    fields = (
        (kinetic, "kinetic wave energy"),
        (strain, "strain wave energy"),
        (total, "total wave energy"),
        (kinetic_fraction, "kinetic fraction"),
    )
    figure, axes_grid = plt.subplots(2, 2, figsize=(12, 9))
    for axes, (values, label) in zip(
        axes_grid.flat,
        fields,
        strict=True,
    ):
        artist = _plot_scalar_field(axes, result, values, label)
        axes.set_title(label)
        _add_scalar_colorbar(
            figure,
            axes,
            artist,
            label,
            result.config.dimensions,
        )
    ####
    figure.suptitle("Scalar-wave energy partition")
    figure.tight_layout()
    figure.savefig(
        output_directory / "wave_energy_partition.png",
        dpi=180,
    )
    plt.close(figure)
####




def _pressure_force_components(
    result: RadiantWaveResult,
) -> tuple[FloatArray, ...]:
    gradients = np.gradient(
        result.wave_pressure,
        *result.config.spacing,
        edge_order=1,
    )
    if result.config.dimensions == 1:
        gradients = (gradients,)
    ####
    return tuple(-np.asarray(gradient) for gradient in gradients)
####




def _save_pressure_force_direction(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    force = _pressure_force_components(result)
    if result.config.dimensions == 1:
        figure, axes_grid = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
        axes_grid[0].plot(result.coordinates[0], result.wave_pressure)
        axes_grid[0].set_ylabel("wave-pressure proxy")
        axes_grid[1].plot(result.coordinates[0], force[0])
        axes_grid[1].axhline(0.0, linewidth=0.8)
        axes_grid[1].set_ylabel("force component")
        axes_grid[1].set_xlabel("position")
        for axes in axes_grid:
            _shade_material_regions(axes, result)
            axes.grid(True, alpha=0.25)
        ####
    else:
        pressure = _central_slice(result.wave_pressure)
        force_x = _central_slice(force[0])
        force_y = _central_slice(force[1])
        magnitude = np.sqrt(force_x * force_x + force_y * force_y)
        extent = (
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        )
        figure, axes_grid = plt.subplots(1, 2, figsize=(13, 6))
        pressure_image = axes_grid[0].imshow(
            pressure.T,
            origin="lower",
            extent=extent,
            aspect="equal",
        )
        stride = max(1, pressure.shape[0] // 18)
        x = result.coordinates[0][::stride]
        y = result.coordinates[1][::stride]
        sampled_magnitude = magnitude[::stride, ::stride]
        visible = sampled_magnitude > 0.05 * float(np.max(magnitude))
        denominator = np.maximum(sampled_magnitude, 1.0e-15)
        direction_x = np.where(
            visible,
            force_x[::stride, ::stride] / denominator,
            np.nan,
        )
        direction_y = np.where(
            visible,
            force_y[::stride, ::stride] / denominator,
            np.nan,
        )
        axes_grid[0].quiver(
            x,
            y,
            direction_x.T,
            direction_y.T,
            angles="xy",
            scale_units="xy",
            scale=16.0,
            width=0.003,
        )
        for boundary in _material_boundaries(result):
            axes_grid[0].axvline(boundary, linewidth=1.0, linestyle="--")
            axes_grid[1].axvline(boundary, linewidth=1.0, linestyle="--")
        ####
        axes_grid[0].set_title("Pressure proxy with −∇p direction")
        axes_grid[0].set_xlabel("x")
        axes_grid[0].set_ylabel("y")
        figure.colorbar(
            pressure_image,
            ax=axes_grid[0],
            label="wave-pressure proxy",
        )

        magnitude_image = axes_grid[1].imshow(
            magnitude.T,
            origin="lower",
            extent=extent,
            aspect="equal",
        )
        axes_grid[1].set_title("In-plane pressure-force magnitude")
        axes_grid[1].set_xlabel("x")
        axes_grid[1].set_ylabel("y")
        figure.colorbar(
            magnitude_image,
            ax=axes_grid[1],
            label="force magnitude",
        )
    ####
    figure.suptitle("Pressure-gradient direction diagnostic")
    figure.tight_layout()
    figure.savefig(
        output_directory / "pressure_force_direction.png",
        dpi=180,
    )
    plt.close(figure)
####




def _centerline(values: FloatArray) -> FloatArray:
    if values.ndim == 1:
        return values
    ####
    return values[:, values.shape[1] // 2]
####




def _save_wave_space_time(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    if len(result.frames) < 2:
        return
    ####
    times = np.array([frame.time for frame in result.frames])
    wave_history = np.stack([_centerline(frame.wave) for frame in result.frames])
    energy_history = np.stack(
        [_centerline(frame.wave_energy) for frame in result.frames]
    )
    extent = (
        -result.config.half_extent,
        result.config.half_extent,
        float(times[0]),
        float(times[-1]),
    )
    wave_bound = max(
        abs(float(np.min(wave_history))),
        abs(float(np.max(wave_history))),
    )
    figure, axes_grid = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
    wave_image = axes_grid[0].imshow(
        wave_history,
        origin="lower",
        extent=extent,
        aspect="auto",
        vmin=-wave_bound,
        vmax=wave_bound,
    )
    energy_image = axes_grid[1].imshow(
        energy_history,
        origin="lower",
        extent=extent,
        aspect="auto",
    )
    for axes in axes_grid:
        for boundary in _material_boundaries(result):
            axes.axvline(boundary, linewidth=1.0, linestyle="--")
        ####
        axes.set_ylabel("time")
    ####
    axes_grid[0].set_title("Signed wave displacement along central x-line")
    axes_grid[1].set_title("Wave energy along central x-line")
    axes_grid[1].set_xlabel("x")
    figure.colorbar(wave_image, ax=axes_grid[0], label="wave displacement")
    figure.colorbar(energy_image, ax=axes_grid[1], label="wave energy")
    left_reflection = (
        result.config.reflector.wave_impedance - result.config.neutral.wave_impedance
    ) / (result.config.reflector.wave_impedance + result.config.neutral.wave_impedance)
    right_reflection = (
        result.config.absorber.wave_impedance - result.config.neutral.wave_impedance
    ) / (result.config.absorber.wave_impedance + result.config.neutral.wave_impedance)
    figure.suptitle("Wave propagation through heterogeneous material interfaces")
    figure.text(
        0.5,
        0.005,
        "Normal-incidence amplitude coefficients: "
        f"neutral→reflector R={left_reflection:+.2f}; "
        f"neutral→loss insert R={right_reflection:+.2f}. "
        "Dashed lines mark interfaces.",
        ha="center",
    )
    figure.tight_layout()
    figure.savefig(output_directory / "wave_space_time.png", dpi=180)
    plt.close(figure)
####




def _cumulative_trapezoid(
    values: FloatArray,
    times: FloatArray,
) -> FloatArray:
    cumulative = np.zeros_like(values)
    if values.shape[0] < 2:
        return cumulative
    ####
    delta_time = np.diff(times)
    increments = 0.5 * (values[1:] + values[:-1]) * delta_time[:, None]
    cumulative[1:] = np.cumsum(increments, axis=0)
    return cumulative
####




def _save_material_energy_history(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    if len(result.frames) < 2:
        return
    ####
    labels = _MATERIAL_LABELS
    times = np.array([frame.time for frame in result.frames])
    energy = np.array([frame.budget.material_wave_energy for frame in result.frames])
    dissipation = np.array(
        [frame.budget.material_wave_dissipation_power for frame in result.frames]
    )
    cumulative_dissipation = _cumulative_trapezoid(dissipation, times)

    figure, axes_grid = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for index, label in enumerate(labels):
        axes_grid[0].plot(times, energy[:, index], label=label)
        axes_grid[1].plot(
            times,
            cumulative_dissipation[:, index],
            label=label,
        )
    ####
    axes_grid[0].set_ylabel("wave energy")
    axes_grid[0].set_title("Wave energy residing in each material")
    axes_grid[1].set_ylabel("cumulative damping loss")
    axes_grid[1].set_xlabel("time")
    axes_grid[1].set_title("Energy removed by material damping")
    for axes in axes_grid:
        axes.grid(True, alpha=0.25)
        axes.legend()
    ####
    figure.suptitle("Reflection, transmission, and absorption accounting")
    figure.tight_layout()
    figure.savefig(
        output_directory / "material_wave_energy_history.png",
        dpi=180,
    )
    plt.close(figure)
####




def _save_coupling_budget_history(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    if len(result.frames) < 2:
        return
    ####
    times = np.array([frame.time for frame in result.frames])
    budgets = [frame.budget for frame in result.frames]
    figure, axes_grid = plt.subplots(3, 2, figsize=(14, 11), sharex=True)

    axes_grid[0, 0].plot(
        times,
        [budget.total_activity for budget in budgets],
    )
    axes_grid[0, 0].set_ylabel("integrated activity")
    axes_grid[0, 0].set_title("Activity state")
    axes_grid[0, 1].plot(
        times,
        [budget.autocatalytic_activity_rate for budget in budgets],
        label="autocatalysis",
    )
    axes_grid[0, 1].plot(
        times,
        [budget.thermal_feedback_activity_rate for budget in budgets],
        label="heat feedback",
    )
    axes_grid[0, 1].plot(
        times,
        [budget.wave_feedback_activity_rate for budget in budgets],
        label="wave-pressure feedback",
    )
    axes_grid[0, 1].plot(
        times,
        [budget.activity_loss_rate for budget in budgets],
        label="loss",
    )
    axes_grid[0, 1].set_ylabel("activity rate")
    axes_grid[0, 1].set_title("Activity production and loss")

    axes_grid[1, 0].plot(
        times,
        [budget.thermal_energy for budget in budgets],
    )
    axes_grid[1, 0].set_ylabel("thermal energy")
    axes_grid[1, 0].set_title("Thermal state")
    axes_grid[1, 1].plot(
        times,
        [budget.heat_source_power for budget in budgets],
        label="source",
    )
    axes_grid[1, 1].plot(
        times,
        [budget.heat_loss_power for budget in budgets],
        label="loss",
    )
    axes_grid[1, 1].set_ylabel("thermal power")
    axes_grid[1, 1].set_title("Heat source and loss")

    axes_grid[2, 0].plot(
        times,
        [budget.total_wave_energy for budget in budgets],
    )
    axes_grid[2, 0].set_ylabel("wave energy")
    axes_grid[2, 0].set_xlabel("time")
    axes_grid[2, 0].set_title("Wave state")
    axes_grid[2, 1].plot(
        times,
        [budget.wave_source_power for budget in budgets],
        label="source work",
    )
    axes_grid[2, 1].plot(
        times,
        [budget.wave_dissipation_power for budget in budgets],
        label="damping loss",
    )
    axes_grid[2, 1].axhline(0.0, linewidth=0.8)
    axes_grid[2, 1].set_ylabel("wave power")
    axes_grid[2, 1].set_xlabel("time")
    axes_grid[2, 1].set_title("Wave source and dissipation")

    for axes in axes_grid.flat:
        axes.grid(True, alpha=0.25)
    ####
    for axes in axes_grid[:, 1]:
        axes.legend()
    ####
    figure.suptitle("Integrated coupling budgets")
    figure.tight_layout()
    figure.savefig(
        output_directory / "coupling_budget_history.png",
        dpi=180,
    )
    plt.close(figure)
####




def _save_balance_factor_history(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    if len(result.frames) < 2:
        return
    ####
    times = np.array([frame.time for frame in result.frames])
    budgets = [frame.budget for frame in result.frames]
    source = np.array([budget.source_strength for budget in budgets])
    sink = np.array([budget.sink_strength for budget in budgets])
    balance = np.array([budget.balance_factor for budget in budgets])

    figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(times, source, label="normalized sources")
    axes[0].plot(times, sink, label="normalized sinks")
    axes[0].set_ylabel("strength")
    axes[0].set_title("Source and sink strengths")
    axes[0].legend()
    axes[1].plot(times, balance, color="tab:purple", label="balance factor")
    axes[1].axhline(1.0, color="black", linestyle="--", linewidth=0.9)
    axes[1].set_ylabel("source / sink")
    axes[1].set_xlabel("time")
    axes[1].set_title("Dimensionless source-to-sink balance diagnostic")
    axes[1].legend()
    for axis in axes:
        axis.grid(True, alpha=0.25)
    ####
    figure.suptitle(
        "Generic balance metric: observational stability signal, not a physical threshold"
    )
    figure.tight_layout()
    figure.savefig(output_directory / "balance_factor_history.png", dpi=180)
    plt.close(figure)
####




def _save_energy_budget_phase_history(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    if len(result.frames) < 2:
        return
    ####
    times = np.array([frame.time for frame in result.frames])
    budgets = [frame.budget for frame in result.frames]
    activity = np.array([budget.total_activity for budget in budgets])
    thermal = np.array([budget.thermal_energy for budget in budgets])
    wave = np.array([budget.total_wave_energy for budget in budgets])
    source = np.array([budget.source_strength for budget in budgets])
    sink = np.array([budget.sink_strength for budget in budgets])
    balance = np.array([budget.balance_factor for budget in budgets])
    heat_source = np.array([budget.heat_source_power for budget in budgets])
    heat_loss = np.array([budget.heat_loss_power for budget in budgets])
    cumulative_source = np.concatenate(
        ([0.0], np.cumsum(np.diff(times) * (source[:-1] + source[1:]) / 2.0))
    )
    cumulative_sink = np.concatenate(
        ([0.0], np.cumsum(np.diff(times) * (sink[:-1] + sink[1:]) / 2.0))
    )
    cumulative_net = cumulative_source - cumulative_sink

    figure, axes_grid = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
    axes = axes_grid.ravel()
    scales = (
        max(float(np.max(activity)), np.finfo(float).tiny),
        max(float(np.max(thermal)), np.finfo(float).tiny),
        max(float(np.max(wave)), np.finfo(float).tiny),
    )
    axes[0].plot(times, activity / scales[0], label="activity")
    axes[0].plot(times, thermal / scales[1], label="thermal energy")
    axes[0].plot(times, wave / scales[2], label="wave energy")
    axes[0].set_ylabel("relative magnitude")
    axes[0].set_title("Stored state trend (each series ÷ its own run maximum)")
    axes[0].legend()

    axes[1].plot(times, thermal, label="thermal energy")
    axes[1].set_ylabel("thermal energy")
    axes[1].set_title("Thermal reservoir and heat transfer")
    heat_axis = axes[1].twinx()
    heat_axis.plot(
        times,
        heat_source,
        color="tab:orange",
        linestyle="--",
        label="heat generation",
    )
    heat_axis.plot(
        times,
        heat_loss,
        color="tab:blue",
        linestyle=":",
        label="heat loss",
    )
    heat_axis.set_ylabel("heat transfer rate")
    lines, labels = axes[1].get_legend_handles_labels()
    extra_lines, extra_labels = heat_axis.get_legend_handles_labels()
    axes[1].legend(lines + extra_lines, labels + extra_labels, loc="upper left")

    axes[2].plot(times, source, label="source rate")
    axes[2].plot(times, sink, label="sink rate")
    axes[2].set_ylabel("rate")
    axes[2].set_title("Instantaneous source, sink, and regulation")
    balance_axis = axes[2].twinx()
    balance_axis.plot(
        times,
        balance,
        color="tab:purple",
        label="balance factor",
    )
    balance_axis.axhline(1.0, color="black", linestyle="--", linewidth=0.8)
    balance_axis.set_ylabel("source / sink")
    lines, labels = axes[2].get_legend_handles_labels()
    extra_lines, extra_labels = balance_axis.get_legend_handles_labels()
    axes[2].legend(lines + extra_lines, labels + extra_labels, loc="upper left")

    axes[3].plot(times, cumulative_source, label="cumulative source")
    axes[3].plot(times, cumulative_sink, label="cumulative sink")
    axes[3].plot(
        times,
        cumulative_net,
        color="tab:red",
        linewidth=2.0,
        label="cumulative net source − sink",
    )
    axes[3].axhline(0.0, color="black", linewidth=0.8)
    axes[3].set_ylabel("integrated normalized budget")
    axes[3].set_xlabel("time")
    axes[3].set_title("Accumulated excess-flow diagnostic")
    axes[3].legend()

    inserted = [frame.absorber_inserted for frame in result.frames]
    if any(inserted) and not all(inserted):
        insertion_time = times[inserted.index(True)]
        for axis in axes:
            axis.axvline(
                insertion_time,
                color="black",
                linestyle="--",
                linewidth=1.0,
            )
        ####
        axes[0].text(
            insertion_time,
            0.96,
            "loss material inserted",
            transform=axes[0].get_xaxis_transform(),
            ha="right",
            va="top",
            fontsize=9,
        )
    ####
    for axis in axes:
        axis.grid(True, alpha=0.25)
    ####
    figure.suptitle(
        "Generic initial → source-dominant buildup → loss-material insertion → "
        "rate regulation trend "
        "(diagnostic units, not conserved physical energy)"
    )
    figure.tight_layout()
    figure.savefig(
        output_directory / "energy_budget_phase_history.png",
        dpi=180,
    )
    plt.close(figure)
####




def _save_absorber_insertion_history(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    inserted_frames = [frame for frame in result.frames if frame.absorber_inserted]
    before_frames = [frame for frame in result.frames if not frame.absorber_inserted]
    if not inserted_frames or not before_frames:
        return
    ####
    before = before_frames[-1].material_id
    after = inserted_frames[-1].material_id
    if before.ndim == 3:
        before = _material_visualization_slice(before, result)
        after = _material_visualization_slice(after, result)
    ####

    colormap = ListedColormap(_MATERIAL_COLORS)
    norm = BoundaryNorm((-0.5, 0.5, 1.5, 2.5, 3.5), colormap.N)
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    for axis, values, title in (
        (axes[0], before, "before insertion"),
        (axes[1], after, "after final insertion depth"),
    ):
        axis.imshow(values.T, origin="lower", cmap=colormap, norm=norm)
        axis.set_title(title)
        axis.set_xlabel("x index")
        axis.set_ylabel(
            "z index" if result.config.material_layout == "channel-block" else "y index"
        )
    ####
    figure.suptitle("Dynamic generic loss-material insertion")
    figure.tight_layout()
    figure.savefig(output_directory / "absorber_insertion.png", dpi=180)
    plt.close(figure)
####




def save_radiant_wave_plots(
    result: RadiantWaveResult,
    output_directory: Path,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    fields = (
        (result.activity, "activity", "activity", False),
        (result.heat, "heat", "heat", False),
        (result.wave, "wave displacement", "wave", True),
        (result.wave_energy, "wave energy density", "wave_energy", False),
        (result.wave_pressure, "wave-pressure proxy", "wave_pressure", False),
        (result.force_magnitude, "pressure-force magnitude", "force", False),
    )
    time_text = f"t = {result.time:.3f}"

    if result.config.dimensions == 1:
        coordinate = result.coordinates[0]
        for values, label, filename, _symmetric in fields:
            _save_line(
                coordinate,
                values,
                label,
                f"1D {label}, {time_text}",
                output_directory / f"{filename}.png",
            )
        ####
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

    _save_material_map(result, output_directory)
    _save_channel_block_geometry(result, output_directory)
    _save_material_property_atlas(result, output_directory)
    _save_coupling_chain(result, output_directory)
    _save_wave_energy_partition(result, output_directory)
    _save_pressure_force_direction(result, output_directory)
    _save_wave_space_time(result, output_directory)
    _save_material_energy_history(result, output_directory)
    _save_coupling_budget_history(result, output_directory)
    _save_balance_factor_history(result, output_directory)
    _save_energy_budget_phase_history(result, output_directory)
    _save_absorber_insertion_history(result, output_directory)

    if result.config.dimensions == 3:
        extent = (
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        )
        for axis, name in enumerate(("x", "y", "z")):
            _save_image(
                np.mean(result.wave_energy, axis=axis),
                extent,
                "mean wave energy density",
                f"3D wave-energy projection along {name}, {time_text}",
                output_directory / f"wave_energy_projection_{name}.png",
            )
        ####
    ####
####




def _save_animation(
    result: RadiantWaveResult,
    field_name: str,
    label: str,
    output_path: Path,
    fps: int,
    *,
    symmetric: bool = False,
) -> None:
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
        (line,) = axes.plot(result.coordinates[0], values[0])
        padding = 0.05 * max(maximum - minimum, 1.0e-12)
        axes.set_xlim(-result.config.half_extent, result.config.half_extent)
        axes.set_ylim(minimum - padding, maximum + padding)
        axes.set_xlabel("position")
        axes.set_ylabel(label)
        axes.grid(True, alpha=0.25)

        def update(index: int) -> tuple[object, ...]:
            line.set_ydata(values[index])
            axes.set_title(f"1D {label}, t = {result.frames[index].time:.3f}")
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
                f"{result.config.dimensions}D central slice: {label}, "
                f"t = {result.frames[index].time:.3f}"
            )
            return (image,)
        ####
    ####


    animation = FuncAnimation(
        figure,
        update,
        frames=len(values),
        interval=1000 / fps,
        blit=False,
    )
    figure.tight_layout()
    animation.save(output_path, writer=PillowWriter(fps=fps), dpi=120)
    plt.close(figure)
####




def _save_material_animation(
    result: RadiantWaveResult,
    output_path: Path,
    fps: int,
) -> None:
    """Animate the material layout so timed insertion is visible in the GIF."""
    values = [frame.material_id for frame in result.frames]
    colormap = ListedColormap(_MATERIAL_COLORS)
    norm = BoundaryNorm((-0.5, 0.5, 1.5, 2.5, 3.5), colormap.N)
    if result.config.dimensions == 1:
        slices = values
        figure, axes = plt.subplots(figsize=(8, 4))
        image = axes.imshow(
            np.asarray(slices[0])[None, :],
            origin="lower",
            aspect="auto",
            extent=(-result.config.half_extent, result.config.half_extent, 0, 1),
            cmap=colormap,
            norm=norm,
        )
        axes.set_yticks([])
        axes.set_xlabel("position")
    else:
        extent = (
            -result.config.half_extent,
            result.config.half_extent,
            -result.config.half_extent,
            result.config.half_extent,
        )
        slices = [_material_visualization_slice(value, result) for value in values]
        figure, axes = plt.subplots(figsize=(7, 6))
        image = axes.imshow(
            slices[0].T,
            origin="lower",
            extent=extent,
            aspect="equal",
            cmap=colormap,
            norm=norm,
        )
        axes.set_xlabel("x")
        axes.set_ylabel(
            "z" if result.config.material_layout == "channel-block" else "y"
        )
    ####
    figure.colorbar(
        image,
        ax=axes,
        ticks=range(len(_MATERIAL_LABELS)),
        label="material: reflector / reactive medium / loss rod / open channel",
    )

    def update(index: int) -> tuple[object, ...]:
        current = np.asarray(slices[index])
        image.set_data(current[None, :] if result.config.dimensions == 1 else current.T)
        inserted = "pre-event"
        progress = result.frames[index].material_event_progress
        if progress:
            labels = result.material_event_names
            inserted = ", ".join(
                f"{name}: {fraction:.0%}"
                for name, fraction in zip(labels, progress, strict=True)
            )
        elif result.frames[index].absorber_inserted:
            inserted = (
                f"loss material: {result.frames[index].absorber_fraction:.0%} "
                "channel depth"
            )
        ####
        axes.set_title(
            f"Material layout, t = {result.frames[index].time:.3f} ({inserted})"
        )
        return (image,)
    ####


    animation = FuncAnimation(
        figure,
        update,
        frames=len(values),
        interval=1000 / fps,
        blit=False,
    )
    figure.tight_layout()
    animation.save(output_path, writer=PillowWriter(fps=fps), dpi=120)
    plt.close(figure)
####




def save_radiant_wave_animations(
    result: RadiantWaveResult,
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
    _save_animation(
        result,
        "wave_pressure",
        "wave-pressure proxy",
        output_directory / "wave_pressure_evolution.gif",
        fps,
    )
    _save_material_animation(
        result,
        output_directory / "material_insertion_evolution.gif",
        fps,
    )
####
