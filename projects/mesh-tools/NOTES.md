# Mesh tools notes

> Type: project note
> Status: needs-review
> Updated: 2026-08-01

## Collection

This directory preserves and organizes the old mesh-tools package:

- Mesh examples and documentation for the maintained Python package under `src/notes_tools/mesh_tools`
- YAML polygon and mesh examples
- Compatibility entry points for runtime and test dependencies
- The original package README

## Exclusions

The original package included a rendered PNG under `examples/rendered/`. It was intentionally not imported. Generated renders and other binary artifacts belong under the ignored `artifacts/` directory or remain outside the repository.

## Caveat

The repository-root `pyproject.toml` is the canonical dependency and test configuration. The local
requirements files delegate to the root extras and must be invoked from the repository root; see the
[setup instructions](README.md#setup-and-run).

This began as preserved source material, but its core Python paths now run in the shared test suite. Review
optional GUI dependencies and the original package assumptions before relying on it in a new application.

From the repository root, the shared validation environment runs its tests with:

```
uv sync --extra test
uv run pytest tests/test_mesh_tools.py
```
