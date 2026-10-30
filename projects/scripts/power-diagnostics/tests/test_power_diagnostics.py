"""Tests for the power-history command builder without launching PowerShell."""

import importlib.util
from pathlib import Path


def load_launcher():
    script = Path(__file__).resolve().parents[1] / "power_history.py"
    spec = importlib.util.spec_from_file_location("power_history", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
####


def test_power_history_launcher_builds_report_command() -> None:
    module = load_launcher()
    arguments = module.build_parser().parse_args(
        ["--report", "--days", "7", "--max-events", "25", "--skip-powercfg"]
    )

    command = module.collector_command(arguments, "pwsh")

    assert command[:5] == ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
    assert "-SkipPowerCfg" in command
    assert "-Days" in command and "7" in command
    assert "-MaxEvents" in command and "25" in command
    assert command[command.index("-OutputDirectory") + 1] == str(Path("artifacts") / "power-diagnostics")
####


def test_console_mode_does_not_request_a_report_directory(tmp_path: Path, monkeypatch) -> None:
    module = load_launcher()
    monkeypatch.chdir(tmp_path)
    arguments = module.build_parser().parse_args([])
    command = module.collector_command(arguments, "pwsh")

    assert command[5].endswith("Get-PowerHistory.ps1")
    assert "-OutputDirectory" not in command
    assert list(tmp_path.iterdir()) == []
####


def test_explicit_and_formatted_report_destinations_are_forwarded(tmp_path: Path) -> None:
    module = load_launcher()
    explicit = tmp_path / "selected"
    report = module.build_parser().parse_args(["--report", "--output-directory", str(explicit)])
    report_command = module.collector_command(report, "pwsh")
    assert report_command[report_command.index("-OutputDirectory") + 1] == str(explicit)

    json_args = module.build_parser().parse_args(["--format", "Json", "--since", "2026-08-19T00:00:00"])
    json_command = module.collector_command(json_args, "pwsh")
    assert json_command[json_command.index("-OutputDirectory") + 1] == str(Path("artifacts") / "power-diagnostics")
    assert json_command[json_command.index("-Since") + 1] == "2026-08-19T00:00:00"
    assert list(tmp_path.iterdir()) == []
####
