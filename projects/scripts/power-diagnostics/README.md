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

Create a complete timestamped report bundle with one command:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

From the repository root, use an explicit ignored output directory:

```shell
python projects/scripts/power-diagnostics/power_history.py --report --output-directory artifacts/power-diagnostics
```

This creates `artifacts/power-diagnostics/YYYYMMDD-HHmmss/` containing JSON,
Markdown, and HTML reports. If the destination is omitted, the launcher uses
`power-reports` relative to the current directory. To choose a history window:

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

For a single output format, use the collector directly:

```shell
python projects/scripts/power-diagnostics/power_history.py --max-events 50
python projects/scripts/power-diagnostics/power_history.py --format Html --output-directory artifacts/power-diagnostics --report-name incident
python projects/scripts/power-diagnostics/power_history.py --format Json --output-directory artifacts/power-diagnostics --report-name incident
```

Use `-Since (Get-Date).AddDays(-7)`, `-Json`, or `-SkipPowerCfg` as needed.
The script does not change power plans, timers, wake permissions, or event
logs. Administrator rights may be required for every event detail.

Run the focused Python command-builder test from the repository root:

```shell
python -m pytest projects/scripts/power-diagnostics/tests
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
