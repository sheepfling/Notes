"""Load the useful geometry subset of Wavefront OBJ into the mesh schema."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .mesh_io import MeshError, TriangularMesh


def _vertex_index(token: str, vertex_count: int) -> int:
    """Convert an OBJ face vertex token to a zero-based vertex index."""

    raw_index = token.split("/", 1)[0]
    try:
        index = int(raw_index)
    except ValueError as error:
        raise MeshError(f"invalid OBJ face vertex token {token!r}") from error
    ####
    if index == 0:
        raise MeshError("OBJ vertex indices are one-based; zero is invalid")
    ####

    resolved = index - 1 if index > 0 else vertex_count + index
    if not 0 <= resolved < vertex_count:
        raise MeshError(
            f"OBJ vertex index {index} is outside the {vertex_count}-vertex array"
        )
    ####
    return resolved
####


def load_obj(path: str | Path) -> TriangularMesh:
    """Load vertices and polygon faces from an OBJ file.

    Texture and normal coordinates are accepted syntactically but ignored. Faces
    with more than three vertices are triangulated as a fan. Negative OBJ vertex
    indices are supported; materials, groups, and free-form curves are ignored.
    """

    source = Path(path)
    vertices: list[list[float]] = []
    faces: list[list[int]] = []

    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise MeshError(f"Could not read OBJ file {source}: {error}") from error
    ####

    for line_number, line in enumerate(lines, start=1):
        fields = line.split()
        if not fields or fields[0].startswith("#"):
            continue
        ####

        if fields[0] == "v":
            if len(fields) < 4:
                raise MeshError(f"line {line_number}: vertex needs three coordinates")
            ####
            try:
                vertices.append([float(value) for value in fields[1:4]])
            except ValueError as error:
                raise MeshError(f"line {line_number}: invalid vertex") from error
            ####
            continue
        ####

        if fields[0] != "f":
            continue
        ####
        if len(fields) < 4:
            raise MeshError(f"line {line_number}: face needs at least three vertices")
        ####

        try:
            polygon = [
                _vertex_index(token, len(vertices)) for token in fields[1:]
            ]
        except MeshError as error:
            raise MeshError(f"line {line_number}: {error}") from error
        ####

        for index in range(1, len(polygon) - 1):
            faces.append([polygon[0], polygon[index], polygon[index + 1]])
        ####
    ####

    try:
        return TriangularMesh(
            vertices=np.asarray(vertices, dtype=np.float64),
            faces=np.asarray(faces, dtype=np.int64),
        )
    except (TypeError, ValueError, MeshError) as error:
        raise MeshError(f"invalid OBJ mesh in {source}: {error}") from error
    ####
####


def to_glsl(mesh: TriangularMesh) -> str:
    """Render a validated triangular mesh as GLSL array declarations."""

    lines = [
        f"const int NUM_VERTICES = {len(mesh.vertices)};",
        f"const int NUM_TRIANGLES = {len(mesh.faces)};",
        "",
        "const vec3 vertices[NUM_VERTICES] = vec3[](",
    ]
    for index, vertex in enumerate(mesh.vertices):
        suffix = "," if index + 1 < len(mesh.vertices) else ""
        x, y, z = (float(coordinate) for coordinate in vertex)
        lines.append(
            f"  vec3({x:.7f}, {y:.7f}, {z:.7f}){suffix}"
        )
    ####
    lines.extend([");", "", "const ivec3 triangles[NUM_TRIANGLES] = ivec3[]("])
    for index, face in enumerate(mesh.faces):
        suffix = "," if index + 1 < len(mesh.faces) else ""
        first, second, third = (int(vertex_index) for vertex_index in face)
        lines.append(f"  ivec3({first}, {second}, {third}){suffix}")
    ####
    lines.append(");")
    return "\n".join(lines)
####
