#!/usr/bin/env python3
"""Handler for checking and applying repository updates."""

import logging
from typing import List, Dict, Any

import requests
import importlib.util
from pathlib import Path

from handlers.base_handler import BaseHandler

_util_path = Path(__file__).resolve().parents[1] / "utility-scripts" / "github_update.py"
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


def fetch_commits_since(repo: str, since_sha: str) -> List[Dict[str, Any]]:
    """Return commits on main after ``since_sha``."""
    url = f"https://api.github.com/repos/{repo}/commits?sha=main"
    commits: List[Dict[str, Any]] = []
    while url:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.error("Error fetching commits: %s", exc)
            break
        data = resp.json()
        for entry in data:
            if entry.get("sha") == since_sha:
                return commits
            msg = entry.get("commit", {}).get("message", "").split("\n", 1)[0]
            commits.append({
                "sha": entry.get("sha"),
                "message": msg,
                "is_merge": msg.lower().startswith("merge"),
            })
        if "next" in resp.links:
            url = resp.links["next"]["url"]
        else:
            break
    return commits


class UpdateHandler(BaseHandler):
    """Provide update information and apply updates."""

    def check_for_update(self) -> Dict[str, Any]:
        last_sha = read_last_sha()
        latest_sha = fetch_latest_sha(REPO)
        has_update = bool(latest_sha and last_sha != latest_sha)
        commits = fetch_commits_since(REPO, last_sha) if has_update else []
        return {
            "has_update": has_update,
            "commits": commits,
            "last_sha": last_sha,
            "latest_sha": latest_sha,
        }

    def handle_get(self) -> Dict[str, Any]:
        return self.check_for_update()

    def handle_post(self, form) -> Dict[str, Any]:
        valid, error_response = self.validate_action(form, "update_repo")
        info = self.check_for_update()
        if not valid:
            error_response.update(info)
            return error_response

        last_sha = info.get("last_sha")
        latest_sha = info.get("latest_sha")
        if not latest_sha or last_sha == latest_sha:
            resp = self.format_success_response("Already up-to-date.")
            resp.update(info)
            return resp

        progress = []
        progress.append("downloading update")
        content = download_zip(REPO)
        if not content:
            resp = self.format_error_response("Error downloading update")
            resp.update(info)
            return resp

        progress.append("extracting update")
        try:
            changed = overlay_from_zip(content, ROOT_DIR)
        except Exception as exc:  # noqa: BLE001
            resp = self.format_error_response(f"Error extracting update: {exc}")
            resp.update(info)
            return resp

        write_last_sha(latest_sha)

        if changed:
            progress.append("installing requirements")
            install_requirements(ROOT_DIR)

        progress.append("restarting server")
        restart_webserver()

        resp = self.format_success_response(f"Updated to {latest_sha}")
        resp.update({"progress": progress, "has_update": False, "commits": []})
        return resp
