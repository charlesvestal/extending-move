#!/usr/bin/env python3
"""Update the local repository with the latest files from GitHub.

This script checks ``last_sha.txt`` for the previously downloaded commit
SHA, retrieves the most recent SHA on the ``main`` branch via the
GitHub API and, if different, downloads and extracts the branch archive
over ``TARGET_DIR``.

Only ``requests`` from PyPI and the Python standard library are used.
"""

from __future__ import annotations

import io
import logging
import os
import shutil
import zipfile
from typing import Optional

import requests

SHA_FILE = "./last_sha.txt"
TARGET_DIR = "/path/to/your/app"

logger = logging.getLogger(__name__)


def get_local_sha(path: str) -> str:
    """Return the SHA stored in ``path`` or an empty string if not found."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            sha = fh.read().strip()
            logger.debug("Local SHA read from %s: %s", path, sha)
            return sha
    except FileNotFoundError:
        logger.info("SHA file not found: %s", path)
        return ""
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.error("Failed to read local SHA: %s", exc)
        return ""


def get_remote_sha(owner: str, repo: str) -> str:
    """Return the latest commit SHA of ``main`` from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/main"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        sha = resp.json().get("sha", "")
        logger.debug("Remote SHA fetched: %s", sha)
        return sha
    except requests.RequestException as exc:
        logger.error("Error fetching remote SHA: %s", exc)
    except ValueError as exc:  # JSON decode error
        logger.error("Invalid JSON response: %s", exc)
    return ""


def _safe_extract(zip_file: zipfile.ZipFile, target_dir: str) -> None:
    """Extract ``zip_file`` to ``target_dir`` stripping the top-level folder."""
    root_prefix = zip_file.namelist()[0].split("/")[0]
    for member in zip_file.infolist():
        name = member.filename
        if name.endswith("/"):
            continue
        relative = os.path.relpath(name, root_prefix)
        if relative.startswith("../"):
            continue
        dest_path = os.path.join(target_dir, relative)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with zip_file.open(member) as src, open(dest_path, "wb") as dst:
            shutil.copyfileobj(src, dst)


def download_and_extract_zip(owner: str, repo: str, target_dir: str) -> None:
    """Download the ``main`` branch archive and unpack it over ``target_dir``."""
    url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            _safe_extract(zf, target_dir)
        logger.info("Archive extracted to %s", target_dir)
    except requests.RequestException as exc:
        logger.error("Error downloading ZIP archive: %s", exc)
        raise
    except zipfile.BadZipFile as exc:
        logger.error("Downloaded file is not a valid ZIP archive: %s", exc)
        raise
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.error("Extraction failed: %s", exc)
        raise


def save_sha(path: str, sha: str) -> None:
    """Persist ``sha`` to ``path``."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(sha)
        logger.info("SHA %s written to %s", sha, path)
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.error("Failed to write SHA file: %s", exc)
        raise


def main() -> None:
    owner, repo = "owner", "repo"
    local = get_local_sha(SHA_FILE)
    remote = get_remote_sha(owner, repo)
    if not remote:
        logger.error("Unable to retrieve remote SHA. Aborting.")
        return
    if local != remote:
        logger.info("Updating from %s to %s", local or "<none>", remote)
        try:
            download_and_extract_zip(owner, repo, TARGET_DIR)
            save_sha(SHA_FILE, remote)
            logger.info("Update complete")
        except Exception:
            logger.error("Update failed")
    else:
        logger.info("Already up-to-date")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
