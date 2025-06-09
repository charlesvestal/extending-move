#!/usr/bin/env python3
"""Utilities for checking and applying updates via git."""
import subprocess
import os
import logging
import tempfile
import shutil
import json
from urllib.request import urlopen

logger = logging.getLogger(__name__)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REMOTE_URL = "https://github.com/charlesvestal/extending-move.git"
DEFAULT_BRANCH = "main"
# GitHub tarball URL for fallback updates
TARBALL_URL = (
    "https://codeload.github.com/charlesvestal/extending-move/tar.gz/refs/heads/main"
)
# Use the static git binary installed in the user's bin directory
GIT_BIN = os.path.expanduser("~/bin/git")


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


def _download_tarball_and_replace():
    """Download the project tarball and replace the repository contents."""
    tmpdir = tempfile.mkdtemp(prefix="update_tarball_")
    tar_path = os.path.join(tmpdir, "repo.tar.gz")
    try:
        downloader = None
        if shutil.which("curl"):
            downloader = ["curl", "-L", "-o", tar_path, TARBALL_URL]
        elif shutil.which("wget"):
            downloader = ["wget", "-O", tar_path, TARBALL_URL]
        else:
            return False, "Neither curl nor wget available for download"
        subprocess.run(downloader, check=True)
        subprocess.run(["tar", "-xzf", tar_path, "-C", tmpdir], check=True)
        extracted = next(
            (d for d in os.listdir(tmpdir) if d.startswith("charlesvestal-")),
            None,
        )
        if not extracted:
            return False, "Extraction failed"
        extracted_path = os.path.join(tmpdir, extracted)
        for name in os.listdir(REPO_DIR):
            if name == ".git":
                continue
            path = os.path.join(REPO_DIR, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        for item in os.listdir(extracted_path):
            shutil.move(os.path.join(extracted_path, item), REPO_DIR)
        return True, "Update completed via tarball"
    except Exception as exc:
        logger.error("Tarball update failed: %s", exc)
        return False, f"Error downloading tarball: {exc}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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
        # Fallback to GitHub API
        try:
            with urlopen(
                f"https://api.github.com/repos/charlesvestal/extending-move/commits/{branch}"
            ) as resp:
                data = json.load(resp)
            return data.get("sha")
        except Exception as exc:
            logger.error("API fetch failed: %s", exc)
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
            logger.warning("Git pull failed; falling back to tarball")
            return _download_tarball_and_replace()
        return True, "Update completed"
    except Exception as exc:
        logger.error("Update failed: %s", exc)
        return False, f"Error during update: {exc}"
