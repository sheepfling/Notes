# Polygon triangulation and mesh display

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

This packet contains a small Python 3.12 mesh-processing toolkit:

- [`triangulate_polygon.py`](../../src/notes_tools/mesh_tools/triangulate_polygon.py): converts a planar polygon with optional holes into
  an indexed triangular mesh.
- [`display_mesh.py`](../../src/notes_tools/mesh_tools/display_mesh.py): displays or renders one or more triangular meshes.
- [`mesh_io.py`](../../src/notes_tools/mesh_tools/mesh_io.py): defines the shared YAML schema, loading, writing, and validation.
- [`obj_io.py`](../../src/notes_tools/mesh_tools/obj_io.py) and [`obj_to_glsl.py`](../../src/notes_tools/mesh_tools/obj_to_glsl.py): load a useful OBJ subset and emit GLSL arrays.

The maintained test entry point is `tests/test_mesh_tools.py` from the repository root.

The scripts use generic Cartesian `X`, `Y`, and `Z` coordinates and one
documented input schema.

## Setup and run

Run these commands from the repository root. The module commands need the
`dev` extra for PyYAML and Shapely. Although the source files include PEP 723
metadata, `python -m` does not use that metadata to install dependencies.
With `uv`, select the extra explicitly:

```shell
uv run --extra dev python -m notes_tools.mesh_tools.triangulate_polygon projects/mesh-tools/examples/example_polygon.yaml artifacts/example_mesh.yaml
uv run --extra dev python -m notes_tools.mesh_tools.display_mesh artifacts/example_mesh.yaml --wireframe --vertices
```

Render without opening a window:

```bash
uv run --extra dev python -m notes_tools.mesh_tools.display_mesh artifacts/example_mesh.yaml \
  --wireframe \
  --save-dir artifacts/mesh-tools/rendered \
  --no-show
```

Alternatively, activate a Python 3.12 virtual environment and install the
repository with `python -m pip install -e ".[dev]"`; then replace
`uv run --extra dev python` with `python` in the commands above. The
[repository setup](../../README.md#validation) includes environment setup.
The tools refuse to replace existing mesh or image files unless `--overwrite`
is supplied. Outputs shown above stay in the ignored `artifacts/` directory.

## Polygon YAML

```yaml
outer_boundary:
  - [0.0, 0.0]
  - [6.0, 0.0]
  - [6.0, 6.0]
  - [0.0, 6.0]
holes:
  - - [0.5, 1.0]
    - [1.0, 2.0]
    - [2.0, 1.5]
```

`outer_boundary` is required. `holes` is optional. A repeated closing point is
accepted and removed. Input winding is normalized automatically.

## Mesh YAML

```yaml
format: triangular_mesh
version: 1
vertices:
  - [0.0, 0.0, 0.0]
  - [1.0, 0.0, 0.0]
  - [0.0, 1.0, 0.0]
faces:
  - [0, 1, 2]
```

Every face contains exactly three zero-based vertex indices. The loader checks
array shapes, finite coordinates, index bounds, repeated indices, and
degenerate triangles.

## OBJ input

The OBJ helper accepts `v` and `f` records, including face tokens such as
`1/2/3`, ignores texture and normal indices, supports negative vertex indices,
and fan-triangulates polygon faces. It intentionally ignores materials,
groups, and non-polygon geometry. Use it when the goal is a small validated mesh
or a GLSL declaration rather than a complete OBJ round trip:

```shell
python -m notes_tools.mesh_tools.obj_to_glsl model.obj --output artifacts/mesh-tools/model.glsl
```

The OBJ converter overwrites an existing output file; omit `--output` to print
the declarations instead. Check the destination before running it.

The old scratch viewer combined OBJ parsing with Open3D, PyVista, and Trimesh.
Those GUI and optional-library integrations remain outside the validated core.

## Tests

```shell
python -m pytest tests/test_mesh_tools.py
```

With `uv`, use `uv run --extra dev python -m pytest tests/test_mesh_tools.py`.

The test suite covers polygon validation, winding normalization, concave
polygons, holes, mesh round-tripping, generic axis labels, both command-line
interfaces, and headless PNG rendering.
