#!/usr/bin/env python3
"""Self-update this repository using GitHub ZIP archives.

The script checks the last seen commit SHA in ``last_sha.txt`` and compares it
with the latest commit on ``main`` fetched via the GitHub API. If a newer
commit is available, the corresponding ZIP archive is downloaded and unpacked
over the current project directory. The new SHA is then stored in
``last_sha.txt`` and the local webserver is restarted.

Set the environment variable ``GITHUB_REPO`` to ``owner/repo`` (defaults to
``charlesvestal/extending-move``) before running if you need to override the
repository.
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests
import subprocess
import signal
import time

REPO = os.environ.get("GITHUB_REPO", "charlesvestal/extending-move")
ROOT_DIR = Path(__file__).resolve().parents[1]
SHA_FILE = ROOT_DIR / "last_sha.txt"


def read_last_sha() -> str:
    try:
        return SHA_FILE.read_text().strip()
    except FileNotFoundError:
        return ""


def write_last_sha(sha: str) -> None:
    SHA_FILE.write_text(f"{sha}\n")


def fetch_latest_sha(repo: str) -> str | None:
    url = f"https://api.github.com/repos/{repo}/commits/main"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json().get("sha")
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching latest SHA: {exc}", file=sys.stderr)
        return None


def download_zip(repo: str) -> bytes | None:
    url = f"https://github.com/{repo}/archive/refs/heads/main.zip"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:  # noqa: BLE001
        print(f"Error downloading ZIP archive: {exc}", file=sys.stderr)
        return None


def overlay_from_zip(content: bytes, root: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zf.extractall(tmpdir)
        extracted_root = next(Path(tmpdir).iterdir())
        shutil.copytree(extracted_root, root, dirs_exist_ok=True)


def restart_webserver() -> None:
    pid_file = ROOT_DIR / "move-webserver.pid"
    log_file = ROOT_DIR / "move-webserver.log"
    port_file = ROOT_DIR / "port.conf"

    pid = None
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass

        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except Exception:
                break
        try:
            pid_file.unlink()
        except Exception:
            pass
    else:
        subprocess.run(["pkill", "-f", "move-webserver.py"], check=False)

    if log_file.exists():
        log_file.unlink()

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT_DIR))
    port = 909
    try:
        if port_file.exists():
            value = int(port_file.read_text().strip())
            if 0 < value < 65536:
                port = value
    except Exception:
        pass

    with open(log_file, "wb") as log:
        subprocess.Popen(
            ["python3", "-u", str(ROOT_DIR / "move-webserver.py")],
            cwd=ROOT_DIR,
            stdout=log,
            stderr=log,
            env=env,
        )
    print(f"Webserver restarted on port {port}")


def update() -> int:
    last_sha = read_last_sha()
    latest_sha = fetch_latest_sha(REPO)
    if not latest_sha:
        return 1

    if last_sha == latest_sha:
        print("Already up-to-date.")
        return 0

    content = download_zip(REPO)
    if not content:
        return 1

    try:
        overlay_from_zip(content, ROOT_DIR)
    except Exception as exc:  # noqa: BLE001
        print(f"Error unpacking ZIP: {exc}", file=sys.stderr)
        return 1

    write_last_sha(latest_sha)
    print(f"Updated to {latest_sha}")
    restart_webserver()
    return 0


if __name__ == "__main__":
    sys.exit(update())
