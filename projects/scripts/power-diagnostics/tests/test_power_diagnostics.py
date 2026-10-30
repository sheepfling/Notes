"""Tests for the power-history command builder without launching PowerShell."""

import importlib.util
from pathlib import Path


def test_power_history_launcher_builds_report_command() -> None:
    script = Path(__file__).resolve().parents[1] / "power_history.py"
    spec = importlib.util.spec_from_file_location("power_history", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    arguments = module.build_parser().parse_args(
        ["--report", "--days", "7", "--max-events", "25", "--skip-powercfg"]
    )

    command = module.collector_command(arguments, "pwsh")

    assert command[:5] == ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
    assert "-SkipPowerCfg" in command
    assert "-Days" in command and "7" in command
    assert "-MaxEvents" in command and "25" in command
####
