#!/usr/bin/env python3
"""Handler for checking and applying repository updates."""

import logging
import os
import time
import subprocess
import sys
from typing import List, Dict, Any, Tuple

import requests
import importlib.util
from pathlib import Path

from handlers.base_handler import BaseHandler

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def _headers() -> dict | None:
    if GITHUB_TOKEN:
        return {"Authorization": f"token {GITHUB_TOKEN}"}
    return None

_util_path = (
    Path(__file__).resolve().parents[1] / "utility-scripts" / "github_update.py"
)
_spec = importlib.util.spec_from_file_location("github_update", _util_path)
github_update = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(github_update)

REPO = github_update.REPO
ROOT_DIR = github_update.ROOT_DIR
read_last_sha = github_update.read_last_sha
write_last_sha = github_update.write_last_sha
fetch_latest_sha = github_update.fetch_latest_sha
download_zip = github_update.download_zip
overlay_from_zip = github_update.overlay_from_zip
install_requirements = github_update.install_requirements
restart_webserver = github_update.restart_webserver

logger = logging.getLogger(__name__)


def fetch_commits_since(
    repo: str, since_sha: str, limit: int = 50
) -> Tuple[List[Dict[str, Any]], bool, str | None]:
    """Return commits on main after ``since_sha`` limited to ``limit`` commits.

    Returns ``(commits, truncated, error_message)`` where ``truncated`` indicates
    more commits are available and ``error_message`` is set if the request fails.
    """
    url = f"https://api.github.com/repos/{repo}/commits?sha=main"
    commits: List[Dict[str, Any]] = []
    truncated = False
    error_message: str | None = None
    headers = _headers()
    while url and len(commits) < limit:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.error("Error fetching commits: %s", exc)
            error_message = "Error fetching commit history"
            break
        data = resp.json()
        for entry in data:
            if entry.get("sha") == since_sha:
                return commits, truncated, error_message
            msg = entry.get("commit", {}).get("message", "").split("\n", 1)[0]
            commits.append(
                {
                    "sha": entry.get("sha"),
                    "message": msg,
                    "is_merge": msg.lower().startswith("merge"),
                }
            )
            if len(commits) >= limit:
                truncated = True
                break
        if len(commits) >= limit or "next" not in resp.links:
            break
        url = resp.links["next"]["url"]
    return commits, truncated, error_message


class UpdateHandler(BaseHandler):
    """Provide update information and apply updates."""

    CACHE_DURATION = 60  # seconds

    def __init__(self) -> None:
        super().__init__()
        self._last_check = 0.0
        self._cached_info: Dict[str, Any] | None = None

    def check_for_update(self) -> Dict[str, Any]:
        now = time.time()
        if self._cached_info and now - self._last_check < self.CACHE_DURATION:
            return self._cached_info

        last_sha = read_last_sha()
        latest_sha = fetch_latest_sha(REPO)
        if not latest_sha:
            info = {
                "has_update": False,
                "commits": [],
                "last_sha": last_sha,
                "latest_sha": None,
                "message": "Error checking for updates. Please try again later.",
                "message_type": "error",
            }
            self._cached_info = info
            self._last_check = now
            return info

        has_update = last_sha != latest_sha
        commits: List[Dict[str, Any]]
        truncated: bool
        commit_error: str | None = None
        if has_update:
            commits, truncated, commit_error = fetch_commits_since(
                REPO, last_sha, limit=50
            )
        else:
            commits, truncated, commit_error = [], False, None
        info = {
            "has_update": has_update,
            "commits": commits,
            "truncated": truncated,
            "last_sha": last_sha,
            "latest_sha": latest_sha,
        }
        if commit_error:
            info["message"] = commit_error
            info["message_type"] = "error"
        self._cached_info = info
        self._last_check = now
        return info

    def handle_get(self) -> Dict[str, Any]:
        return self.check_for_update()

    def handle_post(self, form) -> Dict[str, Any]:
        action = form.getvalue("action")
        info = self.check_for_update()
        if action not in {"update_repo", "restart_server"}:
            return self.format_error_response(
                f"Bad Request: Invalid action '{action}'",
                **info,
            )

        if action == "restart_server":
            log_path = ROOT_DIR / "last-update.log"
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(
                    f"Restart requested {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                log.flush()
                try:
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(_util_path),
                            "--restart-only",
                            "--log",
                            str(log_path),
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception as exc:  # noqa: BLE001
                    log.write(f"Error restarting server: {exc}\n")
                    log.flush()
                    return self.format_error_response(
                        f"Error restarting server: {exc}", **info
                    )
            resp = self.format_success_response(
                "Restarting server...",
                progress=["restarting server"],
                restart_countdown=20,
            )
            resp.update(info)
            return resp

        # action == "update_repo"
        last_sha = info.get("last_sha")
        latest_sha = info.get("latest_sha")
        if not latest_sha or last_sha == latest_sha:
            resp = self.format_success_response("Already up-to-date.")
            resp.update(info)
            return resp

        progress = []
        log_path = ROOT_DIR / "last-update.log"
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(
                f"Update started {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            progress.append("downloading update")
            log.write("downloading update\n")
            log.flush()

            content = download_zip(REPO)
            if not content:
                log.write("Error downloading update\n")
                log.flush()
                resp = self.format_error_response("Error downloading update")
                resp.update(info)
                return resp

            progress.append("extracting update")
            log.write("extracting update\n")
            log.flush()
            try:
                changed = overlay_from_zip(content, ROOT_DIR)
            except Exception as exc:  # noqa: BLE001
                log.write(f"Error extracting update: {exc}\n")
                log.flush()
                resp = self.format_error_response(
                    f"Error extracting update: {exc}"
                )
                resp.update(info)
                return resp

            write_last_sha(latest_sha)

            if changed:
                progress.append("installing requirements")
                log.write("installing requirements\n")
                log.flush()
                install_requirements(ROOT_DIR)

            progress.append("restarting server")
            log.write("restarting server\n")
            log.flush()
            try:
                subprocess.Popen(
                    [
                        sys.executable,
                        str(_util_path),
                        "--restart-only",
                        "--log",
                        str(log_path),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as exc:  # noqa: BLE001
                log.write(f"Error restarting server: {exc}\n")
                log.flush()
                resp = self.format_error_response(
                    f"Error restarting server: {exc}"
                )
                resp.update(info)
                return resp
            log.write("done\n")

        resp = self.format_success_response(f"Updated to {latest_sha}")
        resp.update(
            {
                "progress": progress,
                "has_update": False,
                "commits": [],
                "restart_countdown": 20,
            }
        )
        return resp
