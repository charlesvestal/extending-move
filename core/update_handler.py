#!/usr/bin/env python3
"""Utilities for checking and applying updates via git."""
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REMOTE_URL = "https://github.com/charlesvestal/extending-move.git"
DEFAULT_BRANCH = "main"
# Use bundled static git binary if available
GIT_BIN = os.path.join(REPO_DIR, "bin", "git")


def _run_git_cmd(args):
    """Run a git command in the repository and return output."""
    git_exe = GIT_BIN if os.path.exists(GIT_BIN) else "git"
    try:
        result = subprocess.run(
            [git_exe] + list(args),
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logger.error("Git executable not found: %s", git_exe)
        return None
    except subprocess.CalledProcessError as exc:
        logger.error("Git command failed: %s", exc)
        return None


def _ensure_remote(remote="origin", url=DEFAULT_REMOTE_URL):
    """Ensure the given remote exists; if not, add it."""
    current_url = _run_git_cmd(["remote", "get-url", remote])
    if current_url is None:
        _run_git_cmd(["remote", "add", remote, url])


def get_current_commit():
    """Return the current HEAD commit hash."""
    return _run_git_cmd(["rev-parse", "HEAD"])


def get_latest_remote_commit(remote="origin", branch=DEFAULT_BRANCH):
    """Fetch and return the latest commit hash for the remote branch."""
    _ensure_remote(remote)
    fetch_result = _run_git_cmd(["fetch", remote, branch])
    if fetch_result is None:
        return None
    return _run_git_cmd(["rev-parse", "FETCH_HEAD"])


def check_update_available(remote="origin", branch=DEFAULT_BRANCH):
    """Check if a newer commit exists on the remote."""
    local = get_current_commit()
    latest = get_latest_remote_commit(remote, branch)
    if not local or not latest:
        return False, "Unable to determine update status"
    if local == latest:
        return False, "Already up to date"
    return True, f"Update available: {latest[:7]}"


def perform_update(remote="origin", branch=DEFAULT_BRANCH):
    """Perform a git pull to update the repository."""
    try:
        _ensure_remote(remote)
        _run_git_cmd(["reset", "--hard", "HEAD"])
        pull = _run_git_cmd(["pull", remote, branch])
        if pull is None:
            return False, "Git pull failed"
        return True, "Update completed"
    except Exception as exc:
        logger.error("Update failed: %s", exc)
        return False, f"Error during update: {exc}"
