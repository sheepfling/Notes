"""Build, run, and compare both integer-semantics probes."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def _project_root() -> Path | None:
    """Locate the checked-out C++ and Odin source trees."""
    location = Path(__file__).resolve()
    for parent in location.parents:
        candidate = parent / "projects" / "integer-semantics-lab"
        canonical = parent / "src/notes_tools/integer_semantics/run_lab.py"
        legacy = candidate / "scripts/run_lab.py"
        if (
            canonical.is_file()
            and location in (canonical.resolve(), legacy.resolve())
            and (candidate / "CMakeLists.txt").is_file()
            and (candidate / "odin").is_dir()
        ):
            return candidate
        ####
    ####
    return None
####


ROOT = _project_root()
REPOSITORY_ROOT = ROOT.parents[1] if ROOT is not None else None
REPORTS = (REPOSITORY_ROOT or Path.cwd()) / "artifacts" / "integer-semantics-lab"


def _require_checkout() -> Path:
    if ROOT is None:
        raise RuntimeError("integer semantics runner requires a Notes repository checkout with project assets")
    ####
    return ROOT
####




def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=REPORTS / "build",
    )
    parser.add_argument("--configuration", default="Release")
    parser.add_argument("--skip-odin", action="store_true")
    parser.add_argument("--skip-cpp", action="store_true")
    return parser.parse_args()
####




def run(command: Sequence[str], *, cwd: Path | None = None, stdout: Path | None = None) -> None:
    print("+", " ".join(command))
    if stdout is None:
        subprocess.run(command, cwd=cwd, check=True)
        return
    ####

    stdout.parent.mkdir(parents=True, exist_ok=True)
    with stdout.open("w", encoding="utf-8", newline="\n") as stream:
        subprocess.run(command, cwd=cwd, check=True, stdout=stream, text=True)
    ####
####




def executable_path(build_dir: Path, name: str, configuration: str) -> Path:
    suffixes = (".exe", "") if os.name == "nt" else ("", ".exe")
    candidates = [
        build_dir / configuration / f"{name}{suffix}"
        for suffix in suffixes
    ]
    candidates.extend(build_dir / f"{name}{suffix}" for suffix in suffixes)
    return next((candidate for candidate in candidates if candidate.exists()), candidates[-1])
####




def run_cpp(build_dir: Path, configuration: str) -> Path:
    root = _require_checkout()
    if shutil.which("cmake") is None:
        raise RuntimeError("cmake is required to build the C++ probe")
    ####

    run(
        [
            "cmake",
            "-S",
            str(root),
            "-B",
            str(build_dir),
            f"-DCMAKE_BUILD_TYPE={configuration}",
        ]
    )
    run(["cmake", "--build", str(build_dir), "--config", configuration])
    run(["ctest", "--test-dir", str(build_dir), "--output-on-failure", "-C", configuration])

    executable = executable_path(build_dir, "cpp_integer_semantics", configuration)
    report = REPORTS / "cpp.jsonl"
    run([str(executable), "--format=jsonl", "--catalog=all"], stdout=report)
    return report
####




def run_odin() -> Path:
    root = _require_checkout()
    if shutil.which("odin") is None:
        raise RuntimeError("odin is not on PATH")
    ####

    run(["odin", "test", str(root / "odin"), "-define:ODIN_TEST_THREADS=1"])
    report = REPORTS / "odin.jsonl"
    run(
        ["odin", "run", str(root / "odin"), "--", "--format=jsonl", "--catalog=all"],
        stdout=report,
    )
    return report
####




def main() -> int:
    arguments = parse_args()
    if ROOT is None:
        print("integer semantics runner requires a Notes repository checkout with project assets", file=sys.stderr)
        return 2
    ####
    REPORTS.mkdir(parents=True, exist_ok=True)

    cpp_report: Path | None = None
    odin_report: Path | None = None

    if not arguments.skip_cpp:
        cpp_report = run_cpp(arguments.build_dir, arguments.configuration)
    ####
    if not arguments.skip_odin:
        odin_report = run_odin()
    ####

    if cpp_report is not None and odin_report is not None:
        comparison = REPORTS / "comparison.md"
        run(
            [
                sys.executable,
                str(ROOT / "scripts" / "compare_reports.py"),
                str(odin_report),
                str(cpp_report),
                "--output",
                str(comparison),
            ]
        )
    ####

    return 0
####




if __name__ == "__main__":
    raise SystemExit(main())
####
