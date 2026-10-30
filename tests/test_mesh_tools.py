from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pytest
import yaml

matplotlib.use("Agg")

from notes_tools.mesh_tools.display_mesh import plot_mesh
from notes_tools.mesh_tools.mesh_io import (
    MeshError,
    TriangularMesh,
    load_mesh,
    write_mesh,
)
from notes_tools.mesh_tools.obj_io import load_obj, to_glsl
from notes_tools.mesh_tools.triangulate_polygon import Polygon2D, triangulate_polygon


def signed_area(points: np.ndarray) -> float:
    x_coordinates = points[:, 0]
    y_coordinates = points[:, 1]
    return float(
        0.5
        * np.sum(
            x_coordinates * np.roll(y_coordinates, -1)
            - np.roll(x_coordinates, -1) * y_coordinates
        )
    )
####


def example_polygon() -> Polygon2D:
    return Polygon2D(
        outer_boundary=np.asarray(
            [
                [0.0, 0.0],
                [6.0, 0.0],
                [6.0, 6.0],
                [0.0, 6.0],
            ]
        ),
        holes=(
            np.asarray([[0.5, 1.0], [1.0, 2.0], [2.0, 1.5]]),
            np.asarray([[0.5, 4.0], [1.0, 5.0], [2.0, 4.5]]),
            np.asarray([[3.0, 3.0], [5.0, 3.5], [5.0, 2.5]]),
        ),
    )
####


def test_example_triangulation_counts_area_and_winding() -> None:
    polygon_input = example_polygon()
    mesh = triangulate_polygon(polygon_input)

    assert mesh.vertices.shape == (13, 3)
    assert mesh.faces.shape == (17, 3)
    assert np.all(mesh.vertices[:, 2] == 0.0)

    triangles = mesh.vertices[mesh.faces, :2]
    triangle_areas = np.asarray([signed_area(triangle) for triangle in triangles])
    assert np.all(triangle_areas > 0.0)
    assert float(np.sum(triangle_areas)) == pytest.approx(33.75)
    assert float(np.sum(triangle_areas)) == pytest.approx(
        polygon_input.to_shapely().area
    )
####


def test_polygon_winding_is_normalized() -> None:
    polygon_input = Polygon2D(
        outer_boundary=np.asarray(
            [[0.0, 0.0], [0.0, 4.0], [4.0, 4.0], [4.0, 0.0]]
        ),
        holes=(
            np.asarray([[1.0, 1.0], [3.0, 1.0], [2.0, 3.0]]),
        ),
    )

    assert signed_area(polygon_input.outer_boundary) > 0.0
    assert signed_area(polygon_input.holes[0]) < 0.0
####


def test_concave_polygon_triangulates_at_requested_z() -> None:
    polygon_input = Polygon2D(
        outer_boundary=np.asarray(
            [
                [0.0, 0.0],
                [4.0, 0.0],
                [4.0, 1.0],
                [1.0, 1.0],
                [1.0, 4.0],
                [0.0, 4.0],
            ]
        )
    )

    mesh = triangulate_polygon(polygon_input, z=2.5)

    assert mesh.faces.shape == (4, 3)
    assert np.all(mesh.vertices[:, 2] == 2.5)
####


def test_mesh_yaml_round_trip(tmp_dir: Path) -> None:
    original = triangulate_polygon(example_polygon())
    output_path = tmp_dir / "mesh.yaml"

    write_mesh(output_path, original, metadata={"purpose": "test"})
    restored = load_mesh(output_path)

    assert np.array_equal(restored.vertices, original.vertices)
    assert np.array_equal(restored.faces, original.faces)

    data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert data["format"] == "triangular_mesh"
    assert data["version"] == 1
    assert data["metadata"]["purpose"] == "test"
####


def test_non_current_mesh_schema_is_rejected() -> None:
    with pytest.raises(MeshError, match="format must be"):
        TriangularMesh.from_yaml_data(
            {
                "vertices": [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                ],
                "faces": [[0, 1, 2]],
            }
        )
    ####
####


def test_invalid_hole_is_rejected() -> None:
    with pytest.raises(MeshError, match="invalid"):
        Polygon2D(
            outer_boundary=np.asarray(
                [[0.0, 0.0], [4.0, 0.0], [4.0, 4.0], [0.0, 4.0]]
            ),
            holes=(
                np.asarray([[5.0, 5.0], [6.0, 5.0], [5.5, 6.0]]),
            ),
        )
    ####
####


def test_invalid_face_index_is_rejected() -> None:
    with pytest.raises(MeshError, match="outside the vertex array"):
        TriangularMesh(
            vertices=np.asarray(
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
            ),
            faces=np.asarray([[0, 1, 3]], dtype=np.int64),
        )
    ####
####


@pytest.mark.parametrize(
    "faces",
    [
        [[0.9, 1.9, 2.9]],
        [[-0.1, 1.0, 2.0]],
        [[0.0, 1.0, float("nan")]],
        [[0.0, 1.0, float("inf")]],
        np.asarray([[0, 1, 2**63]], dtype=np.uint64),
        np.asarray([[0, 1, 1.5]], dtype=object),
    ],
)
def test_invalid_face_values_rejected_before_integer_conversion(faces: object) -> None:
    vertices = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    with pytest.raises(MeshError):
        TriangularMesh(vertices=np.asarray(vertices), faces=np.asarray(faces))
    ####
    with pytest.raises(MeshError):
        TriangularMesh.from_yaml_data(
            {"format": "triangular_mesh", "version": 1, "vertices": vertices, "faces": faces}
        )
    ####
####


@pytest.mark.parametrize("faces", [[[0, 1, 2]], [[0.0, 1.0, 2.0]], [["0", "1", "2"]], [[0.0, "1", 2]]])
def test_integral_faces_keep_existing_conversion_behavior(faces: list[list[object]]) -> None:
    data = {
        "format": "triangular_mesh",
        "version": 1,
        "vertices": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        "faces": faces,
    }
    mesh = TriangularMesh.from_yaml_data(data)
    assert mesh.faces.dtype == np.int64
    assert mesh.faces.tolist() == [[0, 1, 2]]
####


def test_obj_loader_handles_slash_negative_indices_and_polygon_fan(tmp_dir: Path) -> None:
    obj_path = tmp_dir / "quad.obj"
    obj_path.write_text(
        "v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf 1/1/1 2/2/1 3/3/1 4/4/1",
        encoding="utf-8",
    )

    mesh = load_obj(obj_path)

    assert mesh.faces.tolist() == [[0, 1, 2], [0, 2, 3]]
    assert "const vec3 vertices[NUM_VERTICES]" in to_glsl(mesh)
####


def test_obj_loader_rejects_zero_index(tmp_dir: Path) -> None:
    obj_path = tmp_dir / "invalid.obj"
    obj_path.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 0 1 2\n",
        encoding="utf-8",
    )

    with pytest.raises(MeshError, match="zero is invalid"):
        load_obj(obj_path)
    ####
####


def test_obj_to_glsl_command_line(tmp_dir: Path) -> None:
    obj_path = tmp_dir / "triangle.obj"
    output_path = tmp_dir / "triangle.glsl"
    obj_path.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
        encoding="utf-8",
    )
    repository_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "notes_tools.mesh_tools.obj_to_glsl",
            str(obj_path),
            "--output",
            str(output_path),
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    rendered = output_path.read_text(encoding="utf-8")
    assert "const vec3 vertices[NUM_VERTICES]" in rendered
    assert "const ivec3 triangles[NUM_TRIANGLES]" in rendered
    assert "ivec3(0, 1, 2)" in rendered
####


def test_plot_uses_generic_axis_labels() -> None:
    mesh = triangulate_polygon(example_polygon())
    figure, axis = plot_mesh(
        mesh,
        title="test",
        wireframe=True,
        show_vertices=True,
    )

    assert axis.get_xlabel() == "X"
    assert axis.get_ylabel() == "Y"
    assert axis.get_zlabel() == "Z"
    figure.canvas.draw()
####


def test_both_command_line_scripts_work(tmp_dir: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    mesh_tools_directory = repository_root / "projects" / "mesh-tools"
    polygon_path = mesh_tools_directory / "example_polygon.yaml"
    if not polygon_path.is_file():
        polygon_path = mesh_tools_directory / "examples" / "example_polygon.yaml"
    ####
    mesh_path = tmp_dir / "example_mesh.yaml"
    image_directory = tmp_dir / "rendered"

    triangulate_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "notes_tools.mesh_tools.triangulate_polygon",
            str(polygon_path),
            str(mesh_path),
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert triangulate_result.returncode == 0, triangulate_result.stderr
    assert mesh_path.is_file()

    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    display_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "notes_tools.mesh_tools.display_mesh",
            str(mesh_path),
            "--wireframe",
            "--vertices",
            "--save-dir",
            str(image_directory),
            "--no-show",
        ],
        cwd=repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert display_result.returncode == 0, display_result.stderr
    assert (image_directory / "example_mesh.png").is_file()
####
