"""Shared YAML schema and validation for indexed triangular meshes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self

import numpy as np
import yaml
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

MESH_FORMAT: Final[str] = "triangular_mesh"
MESH_VERSION: Final[int] = 1


class MeshError(ValueError):
    """Raised when polygon or mesh input is malformed or inconsistent."""


####


@dataclass(frozen=True, slots=True)
class TriangularMesh:
    """An immutable, validated indexed triangular mesh."""

    vertices: FloatArray
    faces: IntArray

    def __post_init__(self) -> None:
        vertices = np.array(self.vertices, dtype=np.float64, copy=True)
        faces = np.array(self.faces, dtype=np.int64, copy=True)

        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise MeshError(
                f"vertices must have shape [vertex_count, 3], got {vertices.shape}."
            )
        ####
        if faces.ndim != 2 or faces.shape[1] != 3:
            raise MeshError(
                f"faces must have shape [face_count, 3], got {faces.shape}."
            )
        ####
        if vertices.shape[0] < 3:
            raise MeshError("A triangular mesh requires at least three vertices.")
        ####
        if faces.shape[0] < 1:
            raise MeshError("A triangular mesh requires at least one face.")
        ####
        if not np.isfinite(vertices).all():
            raise MeshError("vertices contain NaN or infinite coordinates.")
        ####
        if np.any(faces < 0) or np.any(faces >= vertices.shape[0]):
            raise MeshError("faces contain an index outside the vertex array.")
        ####

        repeated_indices = (
            (faces[:, 0] == faces[:, 1])
            | (faces[:, 1] == faces[:, 2])
            | (faces[:, 2] == faces[:, 0])
        )
        if np.any(repeated_indices):
            raise MeshError("faces contain repeated vertex indices.")
        ####

        triangles = vertices[faces]
        doubled_areas = np.linalg.norm(
            np.cross(
                triangles[:, 1] - triangles[:, 0],
                triangles[:, 2] - triangles[:, 0],
            ),
            axis=1,
        )
        scale = max(1.0, float(np.max(np.abs(vertices))))
        area_tolerance = np.finfo(np.float64).eps * scale * scale * 32.0
        if np.any(doubled_areas <= area_tolerance):
            raise MeshError("faces contain a degenerate triangle.")
        ####

        vertices.flags.writeable = False
        faces.flags.writeable = False
        object.__setattr__(self, "vertices", vertices)
        object.__setattr__(self, "faces", faces)
    ####

    @classmethod
    def from_yaml_data(cls, data: object) -> Self:
        """Parse the versioned triangular-mesh YAML schema."""
        if not isinstance(data, Mapping):
            raise MeshError("Mesh YAML must contain a mapping at the top level.")
        ####
        if data.get("format") != MESH_FORMAT:
            raise MeshError(
                f"Mesh YAML format must be {MESH_FORMAT!r}; "
                f"got {data.get('format')!r}."
            )
        ####
        if data.get("version") != MESH_VERSION:
            raise MeshError(
                f"Mesh YAML version must be {MESH_VERSION}; "
                f"got {data.get('version')!r}."
            )
        ####

        try:
            vertices = data["vertices"]
            faces = data["faces"]
        except KeyError as error:
            missing_key = str(error.args[0])
            raise MeshError(f"Mesh YAML is missing required key {missing_key!r}.") from error
        ####

        try:
            return cls(
                vertices=np.asarray(vertices, dtype=np.float64),
                faces=np.asarray(faces, dtype=np.int64),
            )
        except (TypeError, ValueError) as error:
            raise MeshError(f"Mesh arrays contain invalid values: {error}") from error
        ####
    ####

    def to_yaml_data(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        """Return a plain, YAML-serializable representation."""
        data: dict[str, object] = {
            "format": MESH_FORMAT,
            "version": MESH_VERSION,
            "vertices": self.vertices.tolist(),
            "faces": self.faces.tolist(),
        }
        if metadata is not None:
            data["metadata"] = dict(metadata)
        ####
        return data
    ####


####


def load_yaml(path: Path) -> object:
    """Read one UTF-8 YAML document."""
    try:
        with path.open("r", encoding="utf-8") as stream:
            return yaml.safe_load(stream)
        ####
    except OSError as error:
        raise MeshError(f"Could not read {path}: {error}") from error
    except yaml.YAMLError as error:
        raise MeshError(f"Could not parse YAML from {path}: {error}") from error
    ####
####


def load_mesh(path: Path) -> TriangularMesh:
    """Load and validate a triangular mesh from YAML."""
    return TriangularMesh.from_yaml_data(load_yaml(path))
####


def write_mesh(
    path: Path,
    mesh: TriangularMesh,
    *,
    metadata: Mapping[str, object] | None = None,
    overwrite: bool = False,
) -> None:
    """Write a triangular mesh as UTF-8 YAML."""
    if path.exists() and not overwrite:
        raise MeshError(f"Refusing to overwrite existing file: {path}")
    ####

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(
                mesh.to_yaml_data(metadata=metadata),
                stream,
                sort_keys=False,
                allow_unicode=True,
            )
        ####
    except OSError as error:
        raise MeshError(f"Could not write {path}: {error}") from error
    ####
####
