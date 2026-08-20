"""Cross-platform launcher for the Windows power-history report scripts."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIRECTORY = Path(__file__).resolve().parent


def powershell_executable() -> str:
    """Return Windows PowerShell or PowerShell Core, if installed."""
    candidates = ("powershell.exe", "pwsh.exe", "pwsh") if sys.platform == "win32" else ("pwsh",)
    for candidate in candidates:
        executable = shutil.which(candidate)
        if executable:
            return executable
    raise RuntimeError("PowerShell was not found; install PowerShell 7 or run on Windows.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="write a timestamped JSON, Markdown, and HTML bundle")
    parser.add_argument("--days", type=int, default=3, help="history window for --report (default: 3)")
    parser.add_argument("--since", type=str, help="PowerShell-compatible start time, such as 2026-08-19T00:00:00")
    parser.add_argument("--max-events", type=int, default=100)
    parser.add_argument("--format", choices=("Console", "Json", "Markdown", "Html", "All"), default="Console")
    parser.add_argument("--output-directory", type=Path, default=Path("power-reports"))
    parser.add_argument("--report-name", default="power-history")
    parser.add_argument("--skip-powercfg", action="store_true")
    return parser


def collector_command(arguments: argparse.Namespace, executable: str) -> list[str]:
    script_name = "New-PowerReport.ps1" if arguments.report else "Get-PowerHistory.ps1"
    command = [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT_DIRECTORY / script_name)]
    if arguments.report:
        command.extend(["-Days", str(arguments.days), "-MaxEvents", str(arguments.max_events)])
        command.extend(["-OutputDirectory", str(arguments.output_directory)])
    else:
        command.extend(["-MaxEvents", str(arguments.max_events), "-Format", arguments.format])
        if arguments.since:
            command.extend(["-Since", arguments.since])
        if arguments.output_directory != Path("power-reports") or arguments.format != "Console":
            command.extend(["-OutputDirectory", str(arguments.output_directory)])
        command.extend(["-ReportName", arguments.report_name])
    if arguments.skip_powercfg:
        command.append("-SkipPowerCfg")
    return command


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.days < 1 or arguments.max_events < 1:
        raise SystemExit("--days and --max-events must be positive")
    try:
        executable = powershell_executable()
        return subprocess.run(collector_command(arguments, executable), check=False).returncode
    except RuntimeError as error:
        print(f"power-history: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
