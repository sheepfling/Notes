"""Exercise the article runners' CLI and output routing without long simulations."""

import runpy
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("script_name", "default_output"),
    [
        ("reactive_pressure_demo.py", "artifacts/converging-flow/physics-gallery/reactive_pressure"),
        ("impulsive_phase_transition_demo.py", "artifacts/converging-flow/impulsive-phase-transition"),
    ],
)
@pytest.mark.parametrize("explicit", [False, True])
def test_runner_routes_output_and_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    script_name: str,
    default_output: str,
    explicit: bool,
) -> None:
    script = EXAMPLES / script_name
    main = runpy.run_path(str(script), run_name="article_runner_test")["main"]
    calls: list[tuple[Path, str, dict[str, object]]] = []

    def record_run(output: Path, backend: str, **options: object) -> None:
        # Simulate an artifact so routing is checked without running the solver.
        assert output.resolve().is_relative_to(tmp_path.resolve())
        output.mkdir(parents=True)
        (output / "runner-sentinel.txt").write_text("temporary\n", encoding="utf-8")
        calls.append((output, backend, options))
    ####

    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(main.__globals__, "run_demo", record_run)
    arguments = [str(script), "--backend", "numpy", "--resolution", "32", "--frames", "3"]
    if explicit:
        arguments.extend(["--output", "custom/result"])
    ####
    monkeypatch.setattr(sys, "argv", arguments)

    assert main() == 0
    expected = Path("custom/result") if explicit else Path(default_output)
    assert len(calls) == 1
    assert calls[0][0] == expected
    assert calls[0][1] == "numpy"
    assert calls[0][2]["resolution"] == 32
    assert calls[0][2]["snapshot_count"] == 3
    sentinel = tmp_path / expected / "runner-sentinel.txt"
    assert sentinel.read_text(encoding="utf-8") == "temporary\n"
    assert list(tmp_path.rglob("runner-sentinel.txt")) == [sentinel]
####
