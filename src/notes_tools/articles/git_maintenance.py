import argparse
import logging
import os
import subprocess
import sys
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from pathlib import Path
from random import shuffle

log = getLogger(__name__)


def get_git_dir(path: Path) -> Path | None:
    if path.is_symlink() or not path.is_dir():
        return None
    ####
    if path.name == ".git":
        # parent is repo
        log.debug(f'Found possible non-bare repo? {str(path.parent)!r}')
        return path.parent
    ####
    if (
        (path / 'config').is_file()
        and (path / 'HEAD').is_file()
        and (path / 'objects').is_dir()
        and (path / 'refs').is_dir()
    ):
        log.debug(f'Found possible bare repo? {str(path)!r}')
        return path
    ####
    return None
####



def _find_git_repos(base_dir: Path, *, randomized: bool) -> Generator[Path, None, None]:
    """Discover repositories without following symlinks or entering linked worktrees."""
    if base_dir.is_symlink() or not base_dir.is_dir():
        return
    ####
    # A gitfile represents a linked worktree or submodule. Do not update it,
    # or discover nested repositories through it, as part of a broad scan.
    if (base_dir / ".git").is_file():
        return
    ####
    if (git_dir := get_git_dir(base_dir)) is not None:
        yield git_dir
        return
    ####
    paths = sorted(base_dir.iterdir())
    if randomized:
        shuffle(paths)
    ####
    for path in paths:
        if path.is_symlink() or not path.is_dir():
            continue
        ####
        yield from _find_git_repos(path, randomized=randomized)
    ####
####



def find_git_repos(base_dir: Path) -> Generator[Path, None, None]:
    """Recursively find Git repositories in deterministic order."""
    yield from _find_git_repos(base_dir, randomized=False)
####



def find_git_repos_semi_random(base_dir: Path) -> Generator[Path, None, None]:
    """Discover repositories in a shuffled order for parallel updates."""
    yield from _find_git_repos(base_dir, randomized=True)
####



def update_repo(repo_dir: Path) -> bool:
    """Update a Git repository (bare or non-bare)."""
    log.info(f"Updating {str(repo_dir)!r}")

    env = os.environ.copy()
    env["GIT_DISCOVERY_ACROSS_FILESYSTEM"] = "1"

    # Determine if repo is bare
    is_bare_cmd = ["git", "-C", str(repo_dir), "rev-parse", "--is-bare-repository"]
    try:
        log.debug(f'CMD: {is_bare_cmd}')
        is_bare = subprocess.run(
            is_bare_cmd, capture_output=True, text=True, check=True,
            env=env,
        )
        bare = is_bare.stdout.strip() == "true"
    except subprocess.CalledProcessError as e:
        log.error(f"Could not determine if {repo_dir} is bare: {e}")
        return False
    ####
    log.debug(f'Repo is bare? {bare}: {str(repo_dir)!r}')

    if bare:
        cmds = update_commands(repo_dir, bare=True)
    else:
        cmds = update_commands(repo_dir, bare=False)
    ####

    try:
        for cmd in cmds:
            log.debug(f'CMD: {cmd}')
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            if (out := result.stdout.strip()):
                log.info(out)
            ####
            if (err := result.stderr.strip()):
                log.warning(err)
            ####
        ####
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to update {repo_dir}: {e}. cmds: {cmds}")
        return False
    ####

    return True
####


def update_commands(repo_dir: Path, *, bare: bool) -> list[list[str]]:
    """Build a conservative update sequence without changing local work."""

    git = ["git", "-C", str(repo_dir)]
    if bare:
        return [git + ["fetch", "--all", "--tags", "--prune"]]
    ####
    return [
        git + ["fetch", "--tags", "--prune"],
        git + ["pull", "--ff-only"],
    ]
####



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("search_folder", type=Path, help="Root folder to search")
    parser.add_argument('--stdout', action='store_true', help='Logs output to stdout as well')
    parser.add_argument('--log-level', type=int, default=logging.INFO, help='Logging level')
    parser.add_argument('--num-workers', type=int, default=8, help='Number of workers to pull')
    parser.add_argument('--dry-run', action='store_true', help='List targets without running Git or writing a log')

    args = parser.parse_args()

    search_dir = Path(args.search_folder)

    if not search_dir.is_dir():
        print(f"Error: {search_dir} is not a valid directory")
        return 1
    ####

    if search_dir.is_symlink():
        parser.error("search root must not be a symbolic link")
    ####

    if args.dry_run:
        for repo in find_git_repos(search_dir):
            print(repo)
        ####
        return 0
    ####

    # Log file
    handlers: list[logging.Handler] = [logging.FileHandler(search_dir / "git_update.log")]
    if args.stdout:
        handlers.append(logging.StreamHandler(sys.stdout))
    ####

    # Configure logging
    logging.basicConfig(
        handlers=handlers,
        level=int(args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log.debug(f'Args: {args}')

    repos = list(dict.fromkeys(find_git_repos_semi_random(search_dir)))
    if not repos:
        log.info(f'No repos found in {str(search_dir)!r}')
        return 0
    ####

    max_workers = max(1, min(8, args.num_workers))
    futures = {}
    failed = False
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for repo in repos:
            log.debug("Submitting repo to update: %s", repo)
            futures[executor.submit(update_repo, repo)] = repo
        ####

        for future in as_completed(futures):
            repo = futures[future]
            try:
                if future.result():
                    log.info("Repo %s updated successfully", repo)
                else:
                    log.warning("Repo %s update failed", repo)
                    failed = True
                ####
            except Exception:
                log.exception("Exception during repo %s update", repo)
                failed = True
            ####
        ####
    ####
    return 1 if failed else 0
####



if __name__ == "__main__":
    raise SystemExit(main())
####
