# Windows power diagnostics

> Type: project note
> Status: read-only troubleshooting helper

[`Get-PowerHistory.ps1`](Get-PowerHistory.ps1) summarizes recent Windows sleep,
wake, restart, shutdown, crash, and bugcheck evidence. It also runs the
read-only `powercfg` queries useful when diagnosing unexpected sleep or reboot
behavior.

[`power_history.py`](power_history.py) is the recommended entry point. It is
cross-platform and delegates to Windows PowerShell or PowerShell 7, so the
same command works from a Python virtual environment and can fail clearly on
systems without PowerShell.

From the repository root, create a timestamped report bundle in the ignored
artifact directory:

```shell
python projects/scripts/power-diagnostics/power_history.py --report
```

This creates `artifacts/power-diagnostics/YYYYMMDD-HHmmss/` containing JSON,
Markdown, and HTML reports. The default is relative to the current working
directory; from the repository root it is ignored by Git. To choose another
destination or history window:

```shell
python projects/scripts/power-diagnostics/power_history.py --report --days 7 --output-directory artifacts/power-diagnostics
```

Longer windows are supported, subject to the retention limits of the Windows
event logs:

```shell
python projects/scripts/power-diagnostics/power_history.py --report --days 30 --max-events 200 --output-directory artifacts/power-diagnostics
python projects/scripts/power-diagnostics/power_history.py --report --days 365 --max-events 500 --output-directory artifacts/power-diagnostics
```

Some `powercfg` queries require elevated PowerShell rights. If one is denied,
the report still includes all event-log results and records the permission
message for that individual query. Use `--skip-powercfg` when only event
history is needed.

For console output or a single file format, use the Python launcher:

```shell
python projects/scripts/power-diagnostics/power_history.py --max-events 50
python projects/scripts/power-diagnostics/power_history.py --format Html --output-directory artifacts/power-diagnostics --report-name incident
python projects/scripts/power-diagnostics/power_history.py --format Json --output-directory artifacts/power-diagnostics --report-name incident
```

The Python flags `--since`, `--format Json`, and `--skip-powercfg` select a
start time, JSON output, or event-only collection. For direct PowerShell use,
the equivalent collector flags are `-Since`, `-Json`, and `-SkipPowerCfg`:

```powershell
.\projects\scripts\power-diagnostics\Get-PowerHistory.ps1 -Since (Get-Date).AddDays(-7) -SkipPowerCfg
.\projects\scripts\power-diagnostics\Get-PowerHistory.ps1 -Json -OutputDirectory artifacts/power-diagnostics
.\projects\scripts\power-diagnostics\New-PowerReport.ps1 -Days 7 -OutputDirectory artifacts/power-diagnostics
```

The direct report script uses the same `artifacts/power-diagnostics` default
relative to the current working directory. The direct collector requires
`-OutputDirectory` for file formats. Existing `--output-directory` and
`-OutputDirectory` arguments continue to select an explicit destination.
The script does not change power plans, timers, wake permissions, or event
logs. Administrator rights may be required for every event detail.

Run the focused Python command-builder test from the repository root:

```shell
python -m pytest tests/scripts/test_power_diagnostics.py
```

The test inspects arguments only; it does not run PowerShell or collect host
events. Actual event collection remains a Windows-specific operation.

| Event | Meaning |
|---|---|
| System 42 | Entering sleep or connected standby. |
| Power-Troubleshooter 1 / System 107 | Resume and possible wake source. |
| User32 1074 | Planned restart or shutdown, including requester. |
| EventLog 6008 | Previous shutdown was unexpected. |
| Kernel-Power 41 | Restart without a clean shutdown. |
| BugCheck 1001 | Bugcheck/blue-screen information. |
