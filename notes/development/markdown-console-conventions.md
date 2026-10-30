# Console-neutral Markdown command examples

> Type: how-to
> Status: current
> Updated: 2026-08-20

Command examples in general-purpose notes should be usable from both Bash-like
shells and PowerShell whenever the command itself is portable.

## Default style

Use a `shell` fence for portable commands when a language label helps identify
the example, keep each command on one line, and prefer tools that exist on
both platforms:

```shell
python -m pytest
python -m pip install -e ".[dev]"
git status --short
```

A `shell` label describes a command, not a guarantee of compatibility with a
particular console. Existing unlabeled portable examples are also acceptable.
Avoid Bash
line continuations (`\`) and PowerShell backticks in these examples. They make
otherwise portable commands fail when pasted into the other shell.

## Shell-specific style

Use a language label when syntax or behavior is genuinely shell-specific:

```powershell
Get-WinEvent -LogName System -MaxEvents 20
```

```bash
source .venv/bin/activate
```

If both shells need different setup or activation commands, show explicitly
labeled alternatives and keep the shared command separate:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
source .venv/bin/activate
```

Then use an unlabeled fence for the shared command:

```
python -m scripts.ci
```

## Portability checklist

- Prefer `python -m ...` over a platform-specific executable name.
- Prefer forward-slash paths in commands when the tool accepts them.
- Use one-line commands by default; explain a multiline form separately.
- Do not mix PowerShell variables (`$env:NAME`) or Bash variables (`$NAME`)
  into a neutral example.
- Label commands that depend on `cmd.exe`, PowerShell cmdlets, Bash builtins,
  POSIX utilities, or shell-specific quoting.
- Keep the prose clear about the required platform when no portable form
  exists.
