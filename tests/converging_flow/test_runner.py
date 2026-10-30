from __future__ import annotations

from pathlib import Path

from converging_flow import runner


def test_runner_builds_portable_suite_commands(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[list[str]] = []

    def fake_cli_main(arguments: list[str]) -> int:
        calls.append(arguments)
        return 0
    ####

    monkeypatch.setattr(runner, "cli_main", fake_cli_main)

    assert (
        runner.main(
            [
                "--backend",
                "cupy",
                "--reaction-backend",
                "numba",
                "--output-root",
                str(tmp_path),
                "--no-plots",
            ]
        )
        == 0
    )

    assert [call[0] for call in calls] == [
        "suite",
        "reaction-suite",
        "radiant-wave-run",
    ]
    assert all("--no-plots" in call for call in calls)
    assert all("--backend" in call for call in calls)
    assert calls[0][calls[0].index("--backend") + 1] == "cupy"
    assert calls[1][calls[1].index("--backend") + 1] == "numba"
####
