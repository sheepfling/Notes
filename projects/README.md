# Projects

Runnable and preserved source collections live here, separate from the documentation-first `notes/` tree.

Each project keeps its own README, examples, validation notes, and historical caveats where applicable.

## Collections

- [Converging Flow](converging-flow/README.md) — vectorized inert-flow and generic reactive simulation suite.
- [GitLab Docker on macOS](gitlab-docker-macos/README.md) — historical local GitLab and runner experiment.
- [Integer semantics lab](integer-semantics-lab/README.md) — parallel Odin and C++ integer probes.
- [Jorth](jorth/README.md) — a small Forth-like language in JavaScript and Python.
- [Mesh tools](mesh-tools/README.md) — mesh I/O, triangulation, OBJ conversion, and rendering.
- [Point-cloud registration](point-cloud-registration/README.md) — registration metrics and experiments.
- [Script collection](scripts/README.md) — retained Python and Windows compatibility helpers.
- [Shader experiments](shaders/README.md) — GLSL experiments and browser previews.
- [Vector geometry](vector-geometry/README.md) — small geometry helpers.

## Find the tests and outputs

Install the development environment using the [repository setup](../README.md#validation),
then run the commands below from the repository root. Each linked project note
documents its run commands, dependencies, output paths and platform limits.

| Collection | Focused tests | Outputs and limits |
| --- | --- | --- |
| Converging Flow | `python -m pytest tests/converging_flow projects/converging-flow/examples/backend_agnostic/tests projects/converging-flow/examples/physics_diagnostics/tests` | Default outputs under `artifacts/converging-flow/`; GPU tests need CuPy and a device. |
| Integer semantics lab | `python -m pytest projects/integer-semantics-lab/tests` | Python orchestration tests mock compiler runs; actual Odin and C++ execution needs their toolchains. |
| Jorth | `python -m pytest projects/jorth/tests` | Interpreter and cross-language validation; JavaScript checks need Node.js. |
| Mesh tools | `python -m pytest tests/test_mesh_tools.py` | Example mesh and images under `artifacts/`; headless rendering is supported. |
| Point-cloud metrics | `python -m pytest tests/test_point_cloud_metrics.py` | Reusable library; no generated files required. |
| Vector geometry | `python -m pytest tests/test_vector_geometry.py` | Reusable library; no generated files required. |
| Script collection | `python -m pytest projects/scripts tests/test_batch_collection.py` | Each note describes its outputs; Windows batch tests require Windows tools. |
| Shader experiments | `python -m pytest projects/shaders/tests tests/test_shader_gallery.py` | Local browser preview; no committed generated output. |
| GitLab Docker on macOS | See its [historical guide](gitlab-docker-macos/README.md) | Service setup is manual and is not run by the repository test suite. |

The executable notes have focused commands too: [coffee](../notes/thermal/coffee-choice-problem.md)
uses `python -m pytest notes/thermal/tests`, while the [quaternion benchmark](../notes/quaternions/quaternion-performance.md)
uses a separate environment with the recorded dependency versions. Run the complete configured
repository gate with `python -m scripts.ci`. Discovery never starts the historical GitLab service
or the Git maintenance updater.

## Python packages

Maintained reusable Python code is installed from `src/notes_tools`. Project directories contain the
collection-specific source, examples, and historical context rather than acting as import packages.
