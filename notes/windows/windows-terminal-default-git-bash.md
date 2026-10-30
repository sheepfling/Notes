# Set Git Bash as the Windows Terminal default

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

## Purpose

Configure Windows Terminal to open Git Bash when a new default terminal tab is created.

## Prerequisites

- Windows Terminal is installed.
- Git for Windows is installed.
- PowerShell is available.
- Close or restart Windows Terminal after editing its settings.

## Locate the settings file

For the Microsoft Store installation, the settings file is usually:

```text
C:\Users\<user>\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
```

The unpackaged installation may instead use:

```text
C:\Users\<user>\AppData\Local\Microsoft\Windows Terminal\settings.json
```

Check both paths before making changes.

## Locate Git Bash

Common Git for Windows locations are:

```text
C:\Program Files\Git\bin\bash.exe
C:\Program Files (x86)\Git\bin\bash.exe
```

Package managers can use a different path. For example, Scoop installs it at:

```text
C:\Users\<user>\scoop\apps\git\current\bin\bash.exe
```

Resolve the actual executable before adding the profile; do not assume the first path exists.

## Configure it with PowerShell

The following script makes a backup, adds a Git Bash profile if one is not already present, sets that profile as the default, and parses the result to verify valid JSON. Replace the two paths if the installation differs.

```powershell
$settingsPath = 'C:\Users\<user>\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'
$backupPath = "$settingsPath.bak"
$gitPath = 'C:\Users\<user>\scoop\apps\git\current\bin\bash.exe'
$gitGuid = '{9c3f7a5b-6f8b-4e1f-9f44-123456789001}'

Copy-Item -LiteralPath $settingsPath -Destination $backupPath -Force
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json

$gitProfile = @($settings.profiles.list | Where-Object { $_.name -eq 'Git Bash' })[0]
if ($null -eq $gitProfile) {
    $gitProfile = [PSCustomObject]@{
        commandline = $gitPath
        guid        = $gitGuid
        hidden      = $false
        name        = 'Git Bash'
    }
    $settings.profiles.list = @($gitProfile) + @($settings.profiles.list)
} else {
    $gitProfile.guid = $gitGuid
    $gitProfile.commandline = $gitPath
    $gitProfile.hidden = $false
}

$settings.defaultProfile = $gitGuid
$settings | ConvertTo-Json -Depth 20 |
    Set-Content -LiteralPath $settingsPath -Encoding utf8

# Verification
$verified = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
$verified.defaultProfile
$verified.profiles.list | Where-Object name -eq 'Git Bash' |
    Select-Object name, commandline, guid
```

## Verification checklist

1. The settings file parses as JSON without an exception.
2. `defaultProfile` equals the Git Bash profile GUID.
3. The Git Bash profile’s `commandline` points to an existing `bash.exe`.
4. A newly opened Windows Terminal tab starts in Git Bash.

## Recovery

If Terminal behaves unexpectedly, close it and restore the backup:

```powershell
Copy-Item -LiteralPath "$settingsPath.bak" -Destination $settingsPath -Force
```

Then reopen Windows Terminal. The backup is a point-in-time copy, so later Terminal profile changes made after the backup will not be retained.

## Environment record

Applied on 2026-08-01 for a local Windows account:

- Git executable: `C:\Users\<user>\scoop\apps\git\current\cmd\git.exe`
- Git Bash executable: `C:\Users\<user>\scoop\apps\git\current\bin\bash.exe`
- Terminal settings: `C:\Users\<user>\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`
- Backup: same path with `.bak` appended
