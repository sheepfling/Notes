#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "matplotlib>=3.9",
#   "numpy>=2.0",
#   "PyYAML>=6.0",
# ]
# ///
"""Display or render one or more indexed triangular meshes from YAML."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d.axes3d import Axes3D

from .mesh_io import MeshError, TriangularMesh, load_mesh


def equalize_axes(axis: Axes3D) -> None:
    """Give all three displayed axes the same visible scale."""
    limits = np.asarray(
        [axis.get_xlim3d(), axis.get_ylim3d(), axis.get_zlim3d()],
        dtype=np.float64,
    )
    centers = np.mean(limits, axis=1)
    maximum_span = float(np.max(limits[:, 1] - limits[:, 0]))
    if not np.isfinite(maximum_span) or maximum_span <= 0.0:
        maximum_span = 1.0
    ####

    half_span = 0.5 * maximum_span
    axis.set_xlim3d(centers[0] - half_span, centers[0] + half_span)
    axis.set_ylim3d(centers[1] - half_span, centers[1] + half_span)
    axis.set_zlim3d(centers[2] - half_span, centers[2] + half_span)
    axis.set_box_aspect((1.0, 1.0, 1.0))
####


def plot_mesh(
    mesh: TriangularMesh,
    *,
    title: str,
    wireframe: bool = False,
    show_vertices: bool = False,
    elevation: float = 30.0,
    azimuth: float = -60.0,
) -> tuple[Figure, Axes3D]:
    """Create a Matplotlib figure for an arbitrary indexed triangular mesh."""
    figure = plt.figure()
    axis = figure.add_subplot(111, projection="3d")
    if not isinstance(axis, Axes3D):
        raise RuntimeError("Matplotlib did not create a three-dimensional axis.")
    ####

    collection_options: dict[str, Any] = {"alpha": 0.9}
    if wireframe:
        collection_options.update({"edgecolor": "black", "linewidth": 0.6})
    ####

    triangles = mesh.vertices[mesh.faces]
    axis.add_collection3d(Poly3DCollection(triangles, **collection_options))
    axis.auto_scale_xyz(
        mesh.vertices[:, 0],
        mesh.vertices[:, 1],
        mesh.vertices[:, 2],
    )

    if show_vertices:
        axis.scatter(
            mesh.vertices[:, 0],
            mesh.vertices[:, 1],
            mesh.vertices[:, 2],
            s=16.0,
        )
    ####

    axis.set_xlabel("X")
    axis.set_ylabel("Y")
    axis.set_zlabel("Z")
    axis.set_title(title)
    axis.view_init(elev=elevation, azim=azimuth)
    equalize_axes(axis)
    figure.tight_layout()
    return figure, axis
####


def _display_names(paths: Sequence[Path]) -> dict[Path, str]:
    stem_counts: dict[str, int] = {}
    for path in paths:
        stem_counts[path.stem] = stem_counts.get(path.stem, 0) + 1
    ####

    return {
        path: path.stem if stem_counts[path.stem] == 1 else str(path)
        for path in paths
    }
####


def _output_names(paths: Sequence[Path]) -> dict[Path, str]:
    stem_counts: dict[str, int] = {}
    for path in paths:
        stem_counts[path.stem] = stem_counts.get(path.stem, 0) + 1
    ####

    output_names: dict[Path, str] = {}
    for path in paths:
        if stem_counts[path.stem] == 1:
            output_names[path] = f"{path.stem}.png"
        else:
            parent_name = path.parent.name or "mesh"
            output_names[path] = f"{parent_name}_{path.stem}.png"
        ####
    ####
    return output_names
####


def build_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Display or render one or more triangular mesh YAML files."
    )
    parser.add_argument("files", nargs="+", type=Path, help="Mesh YAML files.")
    parser.add_argument(
        "--wireframe",
        action="store_true",
        help="Draw triangle edges.",
    )
    parser.add_argument(
        "--vertices",
        action="store_true",
        help="Draw mesh vertices.",
    )
    parser.add_argument(
        "--elevation",
        type=float,
        default=30.0,
        help="Initial camera elevation in degrees (default: 30).",
    )
    parser.add_argument(
        "--azimuth",
        type=float,
        default=-60.0,
        help="Initial camera azimuth in degrees (default: -60).",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="Save one PNG per mesh into this directory.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=160,
        help="PNG resolution used with --save-dir (default: 160).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing PNG files in --save-dir.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open interactive Matplotlib windows.",
    )
    return parser
####


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    paths: list[Path] = arguments.files
    display_names = _display_names(paths)
    output_names = _output_names(paths)
    figures: list[tuple[Path, Figure]] = []

    try:
        for path in paths:
            mesh = load_mesh(path)
            figure, _ = plot_mesh(
                mesh,
                title=display_names[path],
                wireframe=arguments.wireframe,
                show_vertices=arguments.vertices,
                elevation=arguments.elevation,
                azimuth=arguments.azimuth,
            )
            figures.append((path, figure))
            print(
                f"Loaded {path}: {mesh.vertices.shape[0]} vertices, "
                f"{mesh.faces.shape[0]} faces."
            )
        ####

        if arguments.save_dir is not None:
            arguments.save_dir.mkdir(parents=True, exist_ok=True)
            for path, figure in figures:
                output_path = arguments.save_dir / output_names[path]
                if output_path.exists() and not arguments.overwrite:
                    raise MeshError(
                        f"Refusing to overwrite existing image: {output_path}"
                    )
                ####
                figure.savefig(output_path, dpi=arguments.dpi)
                print(f"Saved {output_path}.")
            ####
        ####
    except (MeshError, OSError) as error:
        for _, figure in figures:
            plt.close(figure)
        ####
        parser.error(str(error))
    ####

    if arguments.no_show:
        for _, figure in figures:
            plt.close(figure)
        ####
    else:
        plt.show()
    ####
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
