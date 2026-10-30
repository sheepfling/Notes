#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from pathlib import Path
from random import shuffle
from typing import Generator

log = getLogger(__name__)


def get_git_dir(path: Path) -> Path | None:
    if not path.is_dir():
        return None
    ####
    if path.name == ".git":
        # parent is repo
        log.debug(f'Found possible non-bare repo? {str(path.parent)!r}')
        return path.parent
    ####
    if path.suffix == '.git' and (path / 'config').is_file() and (path / 'head').is_file():
        log.debug(f'Found possible bare repo? {str(path)!r}')
        return path
    ####
    return None
####



def find_git_repos(base_dir: Path) -> Generator[Path, None, None]:
    """Recursively find all Git repositories under base_dir."""
    for path in base_dir.rglob("*"):
        if (git_dir := get_git_dir(path)) is not None:
            yield git_dir
        ####
    ####
####



def find_git_repos_semi_random(base_dir: Path) -> Generator[Path, None, None]:
    """Recursively find all Git repositories under base_dir."""
    dirs = list(base_dir.iterdir())
    shuffle(dirs)
    for path in dirs:
        if not path.is_dir():
            continue
        ####
        if (git_dir := get_git_dir(path)) is not None:
            yield git_dir
            continue
        ####
        yield from find_git_repos_semi_random(path)
    ####
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



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("search_folder", type=Path, help="Root folder to search")
    parser.add_argument('--stdout', action='store_true', help='Logs output to stdout as well')
    parser.add_argument('--log-level', type=int, default=logging.INFO, help='Logging level')
    parser.add_argument('--num-workers', type=int, default=8, help='Number of workers to pull')

    args = parser.parse_args()

    search_dir = Path(args.search_folder)

    if not search_dir.is_dir():
        print(f"Error: {search_dir} is not a valid directory")
        sys.exit(1)
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
        return
    ####

    max_workers = max(1, min(8, args.num_workers))
    futures = {}
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
                ####
            except Exception:
                log.exception("Exception during repo %s update", repo)
            ####
        ####
    ####
####



if __name__ == "__main__":
    main()
####
