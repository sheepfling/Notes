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

```
python power_history.py --report
```

This creates `power-reports\YYYYMMDD-HHmmss\` containing JSON, Markdown, and
HTML reports. To choose a destination or history window:

```
python power_history.py --report --days 7 --output-directory power-reports
```

Longer windows are supported, subject to the retention limits of the Windows
event logs:

```
python power_history.py --report --days 30 --max-events 200
python power_history.py --report --days 365 --max-events 500
```

Some `powercfg` queries require elevated PowerShell rights. If one is denied,
the report still includes all event-log results and records the permission
message for that individual query. Use `--skip-powercfg` when only event
history is needed.

For a single output format, use the collector directly:

```
python power_history.py --max-events 50
python power_history.py --format Html --output-directory .\power-reports --report-name incident
python power_history.py --format Json --output-directory .\power-reports --report-name incident
```

Use `-Since (Get-Date).AddDays(-7)`, `-Json`, or `-SkipPowerCfg` as needed.
The script does not change power plans, timers, wake permissions, or event
logs. Administrator rights may be required for every event detail.

| Event | Meaning |
|---|---|
| System 42 | Entering sleep or connected standby. |
| Power-Troubleshooter 1 / System 107 | Resume and possible wake source. |
| User32 1074 | Planned restart or shutdown, including requester. |
| EventLog 6008 | Previous shutdown was unexpected. |
| Kernel-Power 41 | Restart without a clean shutdown. |
| BugCheck 1001 | Bugcheck/blue-screen information. |
