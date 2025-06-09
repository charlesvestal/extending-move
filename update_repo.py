#!/usr/bin/env python3
"""Self-update utility for the Move webserver.

This script checks ``last_sha.txt`` for the previously installed commit SHA,
retrieves the latest commit SHA of ``main`` from GitHub and, when different,
downloads the archive and extracts it over the application directory.
After updating it restarts ``move-webserver.py``.

Only ``requests`` from PyPI and the Python standard library are required.
"""

from __future__ import annotations

import io
import logging
import os
import re
import shutil
import signal
import subprocess
import time
import zipfile
from typing import Optional, Tuple

import requests

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SHA_FILE = os.path.join(ROOT_DIR, "last_sha.txt")
LOG_FILE = os.path.join(ROOT_DIR, "move-webserver.log")
PID_FILE = os.path.join(ROOT_DIR, "move-webserver.pid")

logger = logging.getLogger(__name__)


def get_local_sha(path: str) -> str:
    """Return the SHA stored in ``path`` or ``''`` if missing."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            sha = fh.read().strip()
            logger.debug("Local SHA: %s", sha)
            return sha
    except FileNotFoundError:
        logger.info("SHA file not found: %s", path)
        return ""
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.error("Failed to read local SHA: %s", exc)
        return ""


def get_repo_from_git(cwd: str) -> Optional[Tuple[str, str]]:
    """Return (owner, repo) extracted from ``git remote``."""
    try:
        out = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if not out:
            return None
        if out.endswith(".git"):
            out = out[:-4]
        m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+)$", out)
        if m:
            return m.group("owner"), m.group("repo")
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Unable to determine repository from git: %s", exc)
    return None


def get_remote_sha(owner: str, repo: str) -> str:
    """Return the latest commit SHA of ``main`` from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/main"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        sha = resp.json().get("sha", "")
        logger.debug("Remote SHA: %s", sha)
        return sha
    except requests.RequestException as exc:
        logger.error("Error fetching remote SHA: %s", exc)
    except ValueError as exc:  # JSON decode error
        logger.error("Invalid JSON response: %s", exc)
    return ""


def _safe_extract(zf: zipfile.ZipFile, target_dir: str) -> None:
    """Extract ``zf`` to ``target_dir`` stripping the top-level folder."""
    root_prefix = zf.namelist()[0].split("/")[0]
    for member in zf.infolist():
        name = member.filename
        if name.endswith("/"):
            continue
        relative = os.path.relpath(name, root_prefix)
        if relative.startswith("../"):
            continue
        dest = os.path.join(target_dir, relative)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with zf.open(member) as src, open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)
        perm = member.external_attr >> 16
        if perm:
            os.chmod(dest, perm)


def download_and_extract_zip(owner: str, repo: str, target_dir: str) -> None:
    """Download the ``main`` branch archive and unpack it over ``target_dir``."""
    url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        _safe_extract(zf, target_dir)
    logger.info("Archive extracted to %s", target_dir)


def save_sha(path: str, sha: str) -> None:
    """Persist ``sha`` to ``path``."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(sha)
    logger.info("SHA %s written to %s", sha, path)


def restart_webserver(root: str) -> None:
    """Restart ``move-webserver.py`` located in ``root``."""
    pid_file = os.path.join(root, "move-webserver.pid")
    log_file = os.path.join(root, "move-webserver.log")

    # Stop running server if possible
    if os.path.isfile(pid_file):
        try:
            pid = int(open(pid_file).read().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
        except Exception as exc:
            logger.warning("Failed to stop server: %s", exc)
        try:
            os.remove(pid_file)
        except OSError:
            pass

    elif shutil.which("pkill"):
        subprocess.run(["pkill", "-f", "python3 move-webserver.py"], check=False)

    if os.path.exists(log_file):
        os.remove(log_file)

    env = os.environ.copy()
    env["PYTHONPATH"] = root
    log_fh = open(log_file, "w")
    subprocess.Popen([
        "python3",
        "-u",
        "move-webserver.py",
    ], cwd=root, env=env, stdout=log_fh, stderr=subprocess.STDOUT)
    logger.info("Webserver restarted")


def main() -> None:
    repo_info = get_repo_from_git(ROOT_DIR)
    if not repo_info:
        logger.error("Repository origin not found. Aborting update.")
        return
    owner, repo = repo_info

    local = get_local_sha(SHA_FILE)
    remote = get_remote_sha(owner, repo)
    if not remote:
        logger.error("Unable to retrieve remote SHA. Aborting.")
        return
    if local != remote:
        logger.info("Updating from %s to %s", local or "<none>", remote)
        try:
            download_and_extract_zip(owner, repo, ROOT_DIR)
            save_sha(SHA_FILE, remote)
            restart_webserver(ROOT_DIR)
            logger.info("Update complete")
        except Exception as exc:
            logger.error("Update failed: %s", exc)
    else:
        logger.info("Already up-to-date")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
