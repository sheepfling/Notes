# Polygon triangulation and mesh display

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

This packet contains two executable Python 3.12 scripts and one shared module:

- `triangulate_polygon.py`: converts a planar polygon with optional holes into
  an indexed triangular mesh.
- `display_mesh.py`: displays or renders one or more triangular meshes.
- `mesh_io.py`: defines the shared YAML schema, loading, writing, and validation.
- `obj_io.py` and `obj_to_glsl.py`: load a useful OBJ subset and emit GLSL arrays.

The scripts use generic Cartesian `X`, `Y`, and `Z` coordinates and one
documented input schema.

## Run with `uv`

Both executable scripts include PEP 723 dependency metadata:

```console
uv run python -m notes.development.mesh_tools.triangulate_polygon notes/development/mesh_tools/examples/example_polygon.yaml artifacts/example_mesh.yaml
uv run python -m notes.development.mesh_tools.display_mesh artifacts/example_mesh.yaml --wireframe --vertices
```

Render without opening a window:

```console
uv run python -m notes.development.mesh_tools.display_mesh artifacts/example_mesh.yaml \
  --wireframe \
  --save-dir ../../../artifacts/mesh-tools/rendered \
  --no-show
```

When dependencies are already installed, replace `uv run` with `python`.

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

```console
python obj_to_glsl.py model.obj --output model.glsl
```

The old scratch viewer combined OBJ parsing with Open3D, PyVista, and Trimesh.
Those GUI and optional-library integrations remain outside the validated core.

## Tests

```console
pytest -q test_mesh_tools.py
```

The test suite covers polygon validation, winding normalization, concave
polygons, holes, mesh round-tripping, generic axis labels, both command-line
interfaces, and headless PNG rendering.
