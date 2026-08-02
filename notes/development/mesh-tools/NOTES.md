# Mesh tools notes

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

## Collection

This directory preserves and organizes the old mesh-tools package:

- Python mesh I/O, triangulation, display, and test scripts
- YAML polygon and mesh examples
- Runtime and development dependency lists
- The original package README

## Exclusions

The original package included a rendered PNG under `examples/rendered/`. It was intentionally not imported. Generated renders and other binary artifacts belong under the ignored `artifacts/` directory or remain outside the repository.

## Caveat

The `requirements-dev.txt` file refers to `requirements_mesh_tools.txt`, which was not present in the source package. The available `requirements.txt` contains the runtime dependencies. This discrepancy is preserved as a historical note; it has not been silently repaired.

This is preserved source material, not a currently maintained package. Review dependencies and run the tests in an isolated environment before relying on it.

From the repository root, the shared validation environment runs its tests with:

```powershell
uv sync --extra test
uv run pytest notes/development/mesh-tools
```
