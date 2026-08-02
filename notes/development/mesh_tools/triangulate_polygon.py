#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "numpy>=2.0",
#   "PyYAML>=6.0",
#   "shapely>=2.1",
# ]
# ///
"""Triangulate a planar polygon with optional holes into a YAML mesh.

Input schema::

    outer_boundary:
      - [0.0, 0.0]
      - [6.0, 0.0]
      - [6.0, 6.0]
      - [0.0, 6.0]
    holes:
      - - [0.5, 1.0]
        - [1.0, 2.0]
        - [2.0, 1.5]

Contour winding may be clockwise or counter-clockwise. The output uses
counter-clockwise triangle faces in the XY plane.
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import numpy as np
from numpy.typing import NDArray
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon
from shapely.validation import explain_validity

from .mesh_io import MeshError, TriangularMesh, load_yaml, write_mesh

FloatArray = NDArray[np.float64]
Point2D = tuple[float, float]


@dataclass(frozen=True, slots=True)
class Polygon2D:
    """A validated outer boundary and zero or more interior holes."""

    outer_boundary: FloatArray
    holes: tuple[FloatArray, ...] = ()

    def __post_init__(self) -> None:
        outer_boundary = _normalize_ring(
            self.outer_boundary,
            name="outer_boundary",
            counter_clockwise=True,
        )
        holes = tuple(
            _normalize_ring(
                hole,
                name=f"holes[{index}]",
                counter_clockwise=False,
            )
            for index, hole in enumerate(self.holes)
        )
        object.__setattr__(self, "outer_boundary", outer_boundary)
        object.__setattr__(self, "holes", holes)
        self.to_shapely()
    ####

    @classmethod
    def from_yaml_data(cls, data: object) -> Self:
        """Parse the documented polygon YAML schema."""
        if not isinstance(data, Mapping):
            raise MeshError("Polygon YAML must contain a mapping at the top level.")
        ####
        if "outer_boundary" not in data:
            raise MeshError("Polygon YAML is missing required key 'outer_boundary'.")
        ####

        raw_holes = data.get("holes", ())
        if not _is_sequence(raw_holes):
            raise MeshError("'holes' must be a sequence of polygon rings.")
        ####

        try:
            return cls(
                outer_boundary=np.asarray(
                    data["outer_boundary"],
                    dtype=np.float64,
                ),
                holes=tuple(
                    np.asarray(hole, dtype=np.float64) for hole in raw_holes
                ),
            )
        except (TypeError, ValueError) as error:
            raise MeshError(f"Polygon coordinates contain invalid values: {error}") from error
        ####
    ####

    def to_shapely(self) -> Polygon:
        """Build and validate the equivalent Shapely polygon."""
        polygon = Polygon(
            shell=self.outer_boundary,
            holes=[hole.tolist() for hole in self.holes],
        )
        if polygon.is_empty:
            raise MeshError("Polygon is empty.")
        ####
        if polygon.area <= 0.0:
            raise MeshError("Polygon has zero area after subtracting its holes.")
        ####
        if not polygon.is_valid:
            raise MeshError(f"Polygon is invalid: {explain_validity(polygon)}")
        ####
        return polygon
    ####


####


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    )
####


def _signed_area(ring: FloatArray) -> float:
    x_coordinates = ring[:, 0]
    y_coordinates = ring[:, 1]
    return float(
        0.5
        * np.sum(
            x_coordinates * np.roll(y_coordinates, -1)
            - np.roll(x_coordinates, -1) * y_coordinates
        )
    )
####


def _normalize_ring(
    raw_ring: object,
    *,
    name: str,
    counter_clockwise: bool,
) -> FloatArray:
    ring = np.array(raw_ring, dtype=np.float64, copy=True)
    if ring.ndim != 2 or ring.shape[1] != 2:
        raise MeshError(f"{name} must have shape [point_count, 2], got {ring.shape}.")
    ####
    if ring.shape[0] >= 2 and np.array_equal(ring[0], ring[-1]):
        ring = ring[:-1].copy()
    ####
    if ring.shape[0] < 3:
        raise MeshError(f"{name} requires at least three vertices.")
    ####
    if not np.isfinite(ring).all():
        raise MeshError(f"{name} contains NaN or infinite coordinates.")
    ####

    next_ring = np.roll(ring, -1, axis=0)
    if np.any(np.all(ring == next_ring, axis=1)):
        raise MeshError(f"{name} contains consecutive duplicate vertices.")
    ####
    if np.unique(ring, axis=0).shape[0] < 3:
        raise MeshError(f"{name} requires at least three distinct vertices.")
    ####

    signed_area = _signed_area(ring)
    coordinate_scale = max(1.0, float(np.max(np.abs(ring))))
    area_tolerance = np.finfo(np.float64).eps * coordinate_scale**2 * 32.0
    if abs(signed_area) <= area_tolerance:
        raise MeshError(f"{name} has zero area.")
    ####
    if (signed_area > 0.0) != counter_clockwise:
        ring = ring[::-1].copy()
    ####

    ring.flags.writeable = False
    return ring
####


def load_polygon(path: Path) -> Polygon2D:
    """Load and validate a polygon from YAML."""
    return Polygon2D.from_yaml_data(load_yaml(path))
####


def triangulate_polygon(polygon_input: Polygon2D, *, z: float = 0.0) -> TriangularMesh:
    """Compute a constrained Delaunay triangulation."""
    if not np.isfinite(z):
        raise MeshError("z must be finite.")
    ####

    polygon = polygon_input.to_shapely()
    triangle_collection = constrained_delaunay_triangles(polygon)
    triangle_polygons = [
        geometry
        for geometry in triangle_collection.geoms
        if geometry.geom_type == "Polygon" and polygon.covers(geometry)
    ]
    if not triangle_polygons:
        raise MeshError("Triangulation produced no triangles.")
    ####

    vertices_2d: list[Point2D] = []
    vertex_indices: dict[Point2D, int] = {}

    def add_vertex(x_coordinate: float, y_coordinate: float) -> int:
        key = (float(x_coordinate), float(y_coordinate))
        if key in vertex_indices:
            return vertex_indices[key]
        ####
        index = len(vertices_2d)
        vertices_2d.append(key)
        vertex_indices[key] = index
        return index
    ####

    boundary_rings = (polygon_input.outer_boundary, *polygon_input.holes)
    for ring in boundary_rings:
        for point in ring:
            add_vertex(float(point[0]), float(point[1]))
        ####
    ####

    faces: list[tuple[int, int, int]] = []
    for triangle in triangle_polygons:
        coordinates = list(triangle.exterior.coords)[:-1]
        if len(coordinates) != 3:
            raise MeshError(
                "Triangulation returned a non-triangular polygon with "
                f"{len(coordinates)} exterior vertices."
            )
        ####

        face = tuple(
            add_vertex(x_coordinate, y_coordinate)
            for x_coordinate, y_coordinate in coordinates
        )
        triangle_points = np.asarray(coordinates, dtype=np.float64)
        if _signed_area(triangle_points) < 0.0:
            face = (face[0], face[2], face[1])
        ####
        faces.append(face)
    ####

    faces.sort(
        key=lambda triangle_face: (
            sum(vertices_2d[index][0] for index in triangle_face) / 3.0,
            sum(vertices_2d[index][1] for index in triangle_face) / 3.0,
            triangle_face,
        )
    )

    used_indices = {index for face in faces for index in face}
    old_to_new: dict[int, int] = {}
    compact_vertices: list[tuple[float, float, float]] = []
    for old_index, (x_coordinate, y_coordinate) in enumerate(vertices_2d):
        if old_index not in used_indices:
            continue
        ####
        old_to_new[old_index] = len(compact_vertices)
        compact_vertices.append((x_coordinate, y_coordinate, float(z)))
    ####

    compact_faces = [
        tuple(old_to_new[index] for index in face)
        for face in faces
    ]
    mesh = TriangularMesh(
        vertices=np.asarray(compact_vertices, dtype=np.float64),
        faces=np.asarray(compact_faces, dtype=np.int64),
    )

    triangle_points = mesh.vertices[mesh.faces, :2]
    triangle_areas = np.abs(
        0.5
        * (
            triangle_points[:, 0, 0]
            * (triangle_points[:, 1, 1] - triangle_points[:, 2, 1])
            + triangle_points[:, 1, 0]
            * (triangle_points[:, 2, 1] - triangle_points[:, 0, 1])
            + triangle_points[:, 2, 0]
            * (triangle_points[:, 0, 1] - triangle_points[:, 1, 1])
        )
    )
    if not np.isclose(
        float(np.sum(triangle_areas)),
        polygon.area,
        rtol=1.0e-10,
        atol=1.0e-12,
    ):
        raise MeshError(
            "Triangulation area does not match polygon area: "
            f"triangles={np.sum(triangle_areas):.17g}, "
            f"polygon={polygon.area:.17g}."
        )
    ####

    return mesh
####


def build_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Triangulate a planar polygon YAML file into a triangular mesh."
    )
    parser.add_argument("input", type=Path, help="Input polygon YAML file.")
    parser.add_argument("output", type=Path, help="Output mesh YAML file.")
    parser.add_argument(
        "--z",
        type=float,
        default=0.0,
        help="Constant Z coordinate for generated vertices (default: 0).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output file when it already exists.",
    )
    return parser
####


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    try:
        polygon_input = load_polygon(arguments.input)
        polygon = polygon_input.to_shapely()
        mesh = triangulate_polygon(polygon_input, z=arguments.z)
        write_mesh(
            arguments.output,
            mesh,
            metadata={
                "source_file": arguments.input.name,
                "polygon_area": float(polygon.area),
                "plane_z": float(arguments.z),
                "vertex_count": int(mesh.vertices.shape[0]),
                "face_count": int(mesh.faces.shape[0]),
            },
            overwrite=arguments.overwrite,
        )
    except MeshError as error:
        parser.error(str(error))
    ####

    print(
        f"Wrote {mesh.faces.shape[0]} faces and {mesh.vertices.shape[0]} vertices "
        f"to {arguments.output}."
    )
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
