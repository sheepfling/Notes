# Rebuild an MSYS2 environment offline

> Type: reference  
> Status: historical  
> Updated: 2026-08-01

MSYS2 is a rolling distribution, so an offline package bundle is a snapshot rather than a
permanent installer. The useful unit of backup is the package manifest plus the package cache;
the cache contains generated package archives and must remain outside this repository.

## Prepare on a connected MSYS2 installation

Use the shell matching the target environment, such as the MinGW 64-bit shell. Export the
explicitly installed package names and, optionally, the complete package list:

```bash
mkdir -p transfer
pacman -Qqe > transfer/explicitly-installed.txt
pacman -Qq > transfer/all-packages.txt
```

Archive the package cache for transfer. The exact cache path can vary by MSYS2 environment; the
standard pacman cache is shown here:

```bash
tar -czf transfer/msys2-package-cache.tar.gz \
  -C /var/cache/pacman pkg
```

Optionally preserve the pacman database when the goal is to reproduce the same snapshot on a
compatible installation:

```bash
tar -czf transfer/pacman-database.tar.gz \
  -C /var/lib pacman
```

The database is version- and installation-state-specific. Treat it as an optional diagnostic or
snapshot aid, not as a generally portable replacement for installing packages.

## Restore on the offline machine

Install the same MSYS2 family and architecture first, then copy the transfer directory onto the
offline machine. Restore the cache without updating package databases:

```bash
tar -xzf msys2-package-cache.tar.gz -C /var/cache/pacman
```

Do not run `pacman -Sy` or `pacman -Syuu` while offline. Those operations refresh databases from
configured mirrors and can leave an installation in a partially updated state if the network is
unavailable.

If the package database is already suitable, request the explicit package set and rely on the
restored cache:

```bash
pacman -S --needed - < explicitly-installed.txt
```

This succeeds only when compatible package archives and usable database metadata are available.
If pacman wants to download anything, stop and resolve the missing package rather than allowing
an accidental online fallback. A disposable test installation is the safest place to determine
whether a particular cache is complete.

For an exact snapshot, restore the saved database only on a compatible MSYS2 installation and
only after making a backup of the fresh database:

```bash
tar -xzf pacman-database.tar.gz -C /var/lib
```

Do not mix databases from unrelated installations or architectures.

## Recreate a development toolchain

Package names depend on the shell and target architecture. A typical MinGW toolchain might
include GCC, CMake, Ninja or Make, pkg-config, Git, and the project’s native dependencies. Use
the manifest as the source of truth instead of copying a large personal package dump into a
note.

Verify the result:

```bash
pacman -Q
gcc --version
cmake --version
```

Then configure and build a small representative project before restoring larger application
data.

## Caveats

- Keep package archives, compressed caches, and exported databases outside Git; they are binary
  artifacts and can be very large.
- A package cache can contain multiple versions and may not satisfy the current dependency graph.
- Updating an old MSYS2 snapshot later may require a connected, staged upgrade rather than an
  offline replay.
- Preserve checksums and the MSYS2 release date with the transfer media so the snapshot can be
  identified without opening every archive.

See the [MSYS2 project site](https://www.msys2.org/) for current installation and update guidance
before applying an old snapshot to a new machine.
