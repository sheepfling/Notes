# Shrink a WSL2 virtual disk

> Type: how-to  
> Status: current  
> Updated: 2026-08-01

## Purpose

Reclaim Windows disk space after deleting files inside a WSL2 distribution. WSL2 stores each distribution in a dynamically expanding `ext4.vhdx` file. Removing files reduces Linux usage, but does not necessarily reduce the VHDX file’s physical size on Windows.

This procedure compacts the existing VHDX in place. It does not reduce the Linux filesystem’s logical capacity.

## Safety first

- Make a backup before compacting. A simple distribution export is one option:

  ```powershell
  wsl.exe --list --verbose
  wsl.exe --export <DistroName> C:\Backups\<DistroName>-before-compact.tar
  ```

- Close applications using WSL, including terminals, editors, containers, and file-browser windows opened into `\\wsl$`.
- Confirm the target is a WSL2 distribution, not a WSL1 distribution.
- Run the administrative steps from an elevated PowerShell or Command Prompt.

## 1. Check and stop WSL

List distributions and their states:

```powershell
wsl.exe --list --verbose
```

Stop all WSL instances. This is preferable to terminating only one distribution because background WSL processes can keep the VHDX open:

```powershell
wsl.exe --shutdown
```

If a VHDX is still reported as in use, close any remaining WSL-related applications and repeat the shutdown. A reboot may be necessary if Windows still has an open handle.

## 2. Locate the distribution’s `ext4.vhdx`

For Store-installed distributions, the file is usually below:

```text
C:\Users\<user>\AppData\Local\Packages\<distribution-package>\LocalState\ext4.vhdx
```

Examples of package-name prefixes include `CanonicalGroupLimited` for Ubuntu and `TheDebianProject` for Debian. Use the `ext4.vhdx` belonging to the distribution you intend to compact; do not guess when multiple distributions are installed.

A PowerShell search can help locate candidates:

```powershell
Get-ChildItem "$env:LOCALAPPDATA\Packages" -Filter ext4.vhdx -File -Recurse -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty FullName
```

Record the full path before opening DiskPart.

## 3. Compact the VHDX with DiskPart

Open an elevated terminal and start DiskPart:

```text
diskpart
```

At the `DISKPART>` prompt, select the VHDX. Replace the example path with the exact path found above:

```text
select vdisk file="C:\Users\<user>\AppData\Local\Packages\<package>\LocalState\ext4.vhdx"
```

For the safest supported form, attach it read-only, compact it, and detach it:

```text
attach vdisk readonly
compact vdisk
detach vdisk
exit
```

If `attach vdisk readonly` fails because the VHD is already attached, use `detach vdisk` first, then run `compact vdisk` again. The VHD must be detached or attached read-only for compaction to succeed.

## 4. Verify the result

Back in PowerShell, compare the file size:

```powershell
Get-Item -LiteralPath 'C:\Users\<user>\AppData\Local\Packages\<package>\LocalState\ext4.vhdx' |
    Select-Object FullName, Length, LastWriteTime
```

Start the distribution and check that it still boots and that important files are present:

```powershell
wsl.exe -d <DistroName>
```

Inside Linux, check filesystem usage if needed:

```bash
df -h /
```

## Notes and troubleshooting

- The amount reclaimed depends on where free blocks exist inside the dynamically expanding VHDX. Compaction may not reduce the file to exactly the amount reported by `df`.
- `compact vdisk` reclaims unused physical space; it is not the same as shrinking an ext4 partition or changing WSL’s maximum virtual capacity.
- If the command reports that the virtual disk must be detached or read-only, use the `attach vdisk readonly` / `detach vdisk` sequence above.
- If the distribution will not start after an unsuccessful operation, stop troubleshooting changes and restore the exported backup rather than repeatedly modifying the original VHDX.

## References

- Adapted from [How to Shrink a WSL2 Virtual Disk](https://stephenreescarter.net/how-to-shrink-a-wsl2-virtual-disk/) by Stephen Rees-Carter, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- [Microsoft Learn: `compact vdisk`](https://learn.microsoft.com/en-us/Windows-server/administration/windows-commands/compact-vdisk)
- [Microsoft Learn: Manage WSL disk space](https://learn.microsoft.com/en-us/windows/wsl/disk-space)
