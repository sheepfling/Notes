# Integer semantics lab notes

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

This collection preserves the modernized parallel Odin/C++23 integer-semantics experiment, including:

- Odin and C++ probes, tests, and the intentionally separate C++ undefined-behavior lab
- CMake configuration and presets
- Python report runner/comparison utilities
- Shell, PowerShell, and GitHub Actions runners
- Methodology, schema, audit, and validation documents
- The original Odin signedness-discovery snippet

Generated JSONL reports under `artifacts/integer-semantics-lab/` are intentionally ignored. No compiled artifacts or personal paths were imported.

The validation record reports successful C++ builds/tests and no local Odin compiler. Treat the Odin results as CI-validated rather than locally reproduced until an Odin compiler is available.
