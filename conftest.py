"""Keep explicit test paths callable without duplicating broad discovery."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPLICIT_TEST_DIRS = tuple(ROOT / path for path in (
    "notes/thermal/tests",
    "projects/scripts/altchar/tests",
    "projects/scripts/base64/tests",
    "projects/scripts/git-maintenance/tests",
    "projects/scripts/power-diagnostics/tests",
    "projects/scripts/readlines/tests",
    "projects/scripts/textball/tests",
    "projects/scripts/toy-ciphers/tests",
    "projects/scripts/transfer-bundle/tests",
    "projects/jorth/tests",
    "projects/integer-semantics-lab/tests",
    "projects/shaders/tests",
    "projects/converging-flow/examples/backend_agnostic/tests",
    "projects/converging-flow/examples/physics_diagnostics/tests",
    # The benchmark has its own pinned reproduction environment.
    "notes/quaternions/benchmark",
))


def pytest_ignore_collect(collection_path, config):
    """Ignore aliases and pinned tests unless explicitly selected."""
    path = Path(collection_path)
    for explicit_dir in EXPLICIT_TEST_DIRS:
        if path != explicit_dir:
            continue
        ####
        for arg in config.invocation_params.args:
            candidate = str(arg).split("::", 1)[0]
            if candidate.startswith("-"):
                continue
            ####
            requested = Path(candidate).resolve()
            if requested != ROOT and (
                requested == explicit_dir
                or requested in explicit_dir.parents
                or explicit_dir in requested.parents
            ):
                return False
            ####
        ####
        return True
    ####
    return None
####
