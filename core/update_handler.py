import os
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Callable, Optional

import requests
import importlib.util

spec = importlib.util.spec_from_file_location(
    "github_update",
    str((Path(__file__).resolve().parents[1] / "utility-scripts" / "github_update.py")),
)
github_update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(github_update)

REPO = os.environ.get("GITHUB_REPO", "charlesvestal/extending-move")
ROOT_DIR = Path(__file__).resolve().parents[1]
SHA_FILE = ROOT_DIR / "last_sha.txt"


def _read_current_sha() -> str:
    if SHA_FILE.exists():
        return SHA_FILE.read_text().strip()
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT_DIR).decode().strip()
    except Exception:
        return ""


def list_commits_since(current_sha: str, repo: str) -> List[Dict[str, str]]:
    url = f"https://api.github.com/repos/{repo}/compare/{current_sha}...main"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    commits = []
    for c in data.get("commits", []):
        msg = c.get("commit", {}).get("message", "").split("\n")[0]
        is_merge = len(c.get("parents", [])) > 1
        commits.append({"sha": c.get("sha"), "message": msg, "is_merge": is_merge})
    return commits


def check_for_update(repo: str = REPO) -> Tuple[bool, List[Dict[str, str]]]:
    current = _read_current_sha()
    latest = github_update.fetch_latest_sha(repo)
    if not latest or current == latest:
        return False, []
    try:
        commits = list_commits_since(current, repo)
    except Exception:
        commits = []
    return True, commits


def perform_update(progress: Optional[Callable[[str], None]] = None, repo: str = REPO) -> bool:
    def step(msg: str) -> None:
        if progress:
            progress(msg)

    current = _read_current_sha()
    latest = github_update.fetch_latest_sha(repo)
    if not latest or current == latest:
        step("already up-to-date")
        return True

    step("downloading update")
    content = github_update.download_zip(repo)
    if not content:
        step("download failed")
        return False
    step("extracting update")
    try:
        changed = github_update.overlay_from_zip(content, ROOT_DIR)
    except Exception as exc:  # noqa: BLE001
        step(f"error extracting: {exc}")
        return False

    github_update.write_last_sha(latest)
    if changed:
        step("installing requirements")
        github_update.install_requirements(ROOT_DIR)
    step("restarting server")
    github_update.restart_webserver()
    step("update complete")
    return True
