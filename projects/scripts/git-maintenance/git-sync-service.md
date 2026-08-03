# Periodic Git synchronization on Linux or WSL

> Type: how-to  
> Status: needs-review  
> Updated: 2026-08-01

The older note paired a recursive Git updater with a systemd timer. This is a portable version of
that idea using a user service. Replace `<repo-root>` and `<script-path>` with paths on the target
machine; do not paste personal or employer-specific paths into the service file.

## Before enabling automation

[find_and_pull_all_git.py](find_and_pull_all_git.py) discovers ordinary and bare repositories.
The ingested version fixes the original double-update defect and uses a conservative sequence for
working repositories:

1. Fetch remote refs, tags, and pruned branches.
2. Run `git pull --ff-only` without resetting, cleaning, or changing branches.

Uncommitted changes or a non-fast-forward situation therefore cause a repository update to fail
instead of silently deleting local work. Read the log before deciding how to resolve it. The tool
still performs network operations and changes repositories, so test it against a small directory
before scheduling it broadly.

## Create a user service

Install the script somewhere stable, then create
`~/.config/systemd/user/git-sync-pull.service`:

```ini
[Unit]
Description=Fetch and fast-forward Git repositories

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 <script-path>/find_and_pull_all_git.py <repo-root> --stdout --log-level 20
```

The process must have access to the repositories and any credentials needed by their remotes.
Avoid placing tokens in the unit file; use the normal Git credential mechanism for the target
account.

## Schedule it

Create `~/.config/systemd/user/git-sync-pull.timer`:

```ini
[Unit]
Description=Run Git synchronization twice daily

[Timer]
OnCalendar=*-*-* 07:30:00
OnCalendar=*-*-* 16:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Reload and enable the user timer:

```bash
systemctl --user daemon-reload
systemctl --user enable --now git-sync-pull.timer
systemctl --user status git-sync-pull.timer
systemctl --user list-timers git-sync-pull.timer
```

For WSL, systemd must be enabled for the distribution and the user session must be available.
If the service needs to run without an interactive login, investigate user lingering for that
machine rather than copying a system-wide service recipe blindly.

## Verify and troubleshoot

Run one repository manually first:

```bash
python3 <script-path>/find_and_pull_all_git.py <small-test-root> --stdout --log-level 10 --num-workers 1
```

Then inspect the generated `git_update.log` under the search root. Common causes of failure are
missing credentials, a dirty working tree, a branch that cannot be fast-forwarded, a remote that
no longer exists, and a bare repository with no configured remote.

The timer is a convenience for personal mirrors, not a replacement for backups or a reviewable
deployment pipeline. Keep the search root narrow and exclude repositories where automated pulls
would be unsafe.
