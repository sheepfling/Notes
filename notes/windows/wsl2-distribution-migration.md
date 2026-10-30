# Move a WSL2 distribution to another drive

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

Exporting and importing a distribution is a safer way to relocate its virtual disk than copying
an open `VHDX`. The export is a generated backup artifact; keep it outside Git and verify it before
unregistering the original distribution.

## Plan the move

Choose a destination with enough space for both the exported tar file and the imported
distribution. Use a temporary distribution name and location for the test import. Do not reuse a
name or directory that contains another distribution.

List the current distributions and confirm the source is WSL2:

```powershell
wsl.exe --list --verbose
```

## Export and test-import

Stop WSL completely, then export the named distribution to a backup location:

```powershell
wsl.exe --shutdown
wsl.exe --export <DistroName> D:\WSL\<DistroName>-backup.tar
```

Import a temporary copy with WSL2 enabled:

```powershell
wsl.exe --import <DistroName>-test D:\WSL\<DistroName>-test D:\WSL\<DistroName>-backup.tar --version 2
```

Start the test copy and inspect important files, installed packages, services, network
configuration, and application data:

```powershell
wsl.exe -d <DistroName>-test
```

When the test is complete, leave the shell and remove only the temporary registration:

```powershell
wsl.exe --unregister <DistroName>-test
```

`wsl --unregister` permanently removes the selected distribution and its imported filesystem.
Confirm the name with `wsl --list --verbose` before running it.

## Replace the original

After the test import succeeds and the backup tar has been checked, unregister the original:

```powershell
wsl.exe --unregister <DistroName>
```

Import the backup under the original name at its new location:

```powershell
wsl.exe --import <DistroName> D:\WSL\<DistroName> D:\WSL\<DistroName>-backup.tar --version 2
```

Start it and verify the application data again:

```powershell
wsl.exe -d <DistroName>
```

Keep the export until the new installation has survived a reboot and a normal work session.

## Set the default Linux user

An imported distribution may start as `root`. For an imported distribution, set the default
user in `/etc/wsl.conf` rather than relying on a launcher-specific `distro.exe config` command:

```ini
[user]
default=<linux-user>
```

Then leave the distribution and restart WSL:

```powershell
wsl.exe --shutdown
wsl.exe -d <DistroName>
```

If systemd or mirrored networking was part of the original setup, preserve those settings only
after confirming they are appropriate for the new WSL release and host configuration.

## Verification and recovery

- Check `wsl.exe --list --verbose` for the expected name, state, and version.
- Confirm the default user, mounted drives, services, SSH configuration, and important files.
- Reconnect Docker or other host integrations only after the distribution itself is healthy.
- Do not delete the export until the new distribution is backed up independently.
- If the new import fails, stop and restore from the export instead of repeatedly unregistering
  and re-importing the only copy.

This procedure moves logical distribution contents. It does not preserve every host-side
registration detail, Windows Terminal profile, or external integration automatically.
