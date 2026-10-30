# PyVista scratch-gallery notes

> Type: collection  
> Status: historical  
> Updated: 2026-08-01

The old `scratch/pyvista` directory was primarily a local copy of PyVista gallery examples rather
than a coherent application. It mixed lighting, animation, volume rendering, streamlines,
colormaps, magnetic-field data, OpenFOAM cooling data, and an eigenmode demonstration. These
examples are useful as a map of ideas, but they depend on a GUI backend, optional VTK features,
and in several cases remote example datasets.

## What each cluster was exploring

| Cluster                                                                       | Durable idea                                                                                                                                                                            |
|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `pyvista_animate_minimal_example.py`                                          | A plotter callback can update mesh state on a timer; keep simulation state outside the callback and make the update deterministic when testing.                                         |
| `pyvista_light_actors.py`, `pyvista_mesh_lighting.py`, and `pyvista_scrap.py` | Camera, scene, and spotlight lighting have different coordinate conventions; choose a camera explicitly when inspecting large light cones.                                              |
| `pyvista_moving_cmap.py`                                                      | A scalar field can be recomputed or remapped per frame without rebuilding the geometry. Separate field generation from rendering.                                                       |
| `pyvista_magnetic.py` and `pyvista_openfoam_cooling.py`                       | Streamlines, clipping, scalar coloring, and volume rendering are complementary views of vector/scalar fields. Dataset downloads make these demos unsuitable for offline CI by default.  |
| `pyvista_volumetric.py`                                                       | Volume rendering benefits from an explicit opacity transfer function and a cropped region of interest for large data.                                                                   |
| `pyvista_warp_by_vector_eignenmodes.py`                                       | A modal displacement field can be attached to a structured grid and displayed with `warp_by_vector`; numerical eigenmode computation should be validated independently of the renderer. |
| `pyvista_scratch.py`                                                          | A mixed mesh/heat-hotspot experiment. Its OBJ/GLSL conversion is now covered by the [mesh-tools collection](../../projects/mesh-tools/README.md); the GUI-specific viewer was not copied.              |

## A small animation contract

For a useful, testable animation, define the state transition separately from the plotter:

```python
def advance(points, step, amplitude):
    """Return the next point positions without mutating the input."""
    next_points = points.copy()
    next_points[:, 2] += amplitude * step
    return next_points
```

The rendering callback can then assign the result to a mesh and request a redraw. Unit-test the
state transition with ordinary NumPy before opening a window. Save screenshots or movies under
ignored `artifacts/`, never beside the note or source script.

## Why the raw examples are not copied here

The source files were mostly third-party gallery material with no local test harness, and some
download data or open an interactive window. Copying them into a personal archive would freeze
version-sensitive API calls without adding durable explanation. Use the [current PyVista examples
gallery](https://docs.pyvista.org/examples/) when a particular visualization is needed, and copy
only a small, attributed example into a project with its dependency and version pinned.
