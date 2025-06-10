#!/usr/bin/env python3
"""Self-update this repository using GitHub ZIP archives.

The script checks the last seen commit SHA in ``last_sha.txt`` and compares it
with the latest commit on ``main`` fetched via the GitHub API. If a newer
commit is available, the corresponding ZIP archive is downloaded and unpacked
over the current project directory. The new SHA is then stored in
``last_sha.txt`` and the local webserver is restarted. If ``requirements.txt``
changed, the script runs ``pip install --no-cache-dir -r requirements.txt``
after setting ``TMPDIR=/data/UserData/tmp`` before restarting the server.

Set the environment variable ``GITHUB_REPO`` to ``owner/repo`` (defaults to
``charlesvestal/extending-move``) before running if you need to override the
repository.

If ``last_sha.txt`` is missing, the updater treats it as an empty string and
always fetches the latest commit.
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
import hashlib

import requests
import subprocess
import signal
import time

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def _headers() -> dict | None:
    if GITHUB_TOKEN:
        return {"Authorization": f"token {GITHUB_TOKEN}"}
    return None


REPO = os.environ.get("GITHUB_REPO", "charlesvestal/extending-move")
ROOT_DIR = Path(__file__).resolve().parents[1]
SHA_FILE = ROOT_DIR / "last_sha.txt"
# Directory for temporary extraction; defaults to repo root if not provided
TMP_DIR_PATH = Path(
    os.environ.get("UPDATE_TMPDIR") or os.environ.get("TMPDIR", str(ROOT_DIR))
)


def read_last_sha() -> str:
    """Return the last updated SHA or ``""`` if the file is missing."""
    try:
        return SHA_FILE.read_text().strip()
    except FileNotFoundError:
        return ""


def write_last_sha(sha: str) -> None:
    SHA_FILE.write_text(f"{sha}\n")


def fetch_latest_sha(repo: str) -> str | None:
    url = f"https://api.github.com/repos/{repo}/commits/main"
    headers = _headers()
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get("sha")
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching latest SHA: {exc}", file=sys.stderr)
        return None


def download_zip(repo: str) -> bytes | None:
    url = f"https://github.com/{repo}/archive/refs/heads/main.zip"
    headers = _headers()
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:  # noqa: BLE001
        print(f"Error downloading ZIP archive: {exc}", file=sys.stderr)
        return None


def _hash_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def overlay_from_zip(content: bytes, root: Path) -> bool:
    """Return True if requirements.txt changed."""
    with tempfile.TemporaryDirectory(dir=str(TMP_DIR_PATH)) as tmpdir:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zf.extractall(tmpdir)
        extracted_root = next(Path(tmpdir).iterdir())
        old_hash = _hash_file(root / "requirements.txt")
        new_hash = _hash_file(extracted_root / "requirements.txt")
        shutil.copytree(extracted_root, root, dirs_exist_ok=True)
    return old_hash != new_hash


def install_requirements(root: Path) -> None:
    req = root / "requirements.txt"
    if not req.exists():
        return
    env = os.environ.copy()
    env.setdefault("TMPDIR", "/data/UserData/tmp")
    print(f"TMPDIR is set to: {env['TMPDIR']}")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", str(req)],
            check=True,
            env=env,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error installing requirements: {exc}", file=sys.stderr)


def restart_webserver(log: io.TextIOBase | None = None) -> None:
    pid_file = ROOT_DIR / "move-webserver.pid"
    log_file = ROOT_DIR / "move-webserver.log"
    port_file = ROOT_DIR / "port.conf"

    def log_msg(msg: str) -> None:
        if log is not None:
            log.write(msg + "\n")
            log.flush()
        else:
            print(msg)

    log_msg("Restarting the webserver...")
    pid = None
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
        except Exception:
            pid = None

    same_process = pid == os.getpid()

    if pid and not same_process:
        try:
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
    elif not pid:
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

    if same_process:
        log_msg("Starting the webserver (exec)...")
        with open(log_file, "wb") as log_f:
            os.dup2(log_f.fileno(), sys.stdout.fileno())
            os.dup2(log_f.fileno(), sys.stderr.fileno())
            os.execvpe(
                "python3",
                ["python3", "-u", str(ROOT_DIR / "move-webserver.py")],
                env,
            )
        return
    else:
        with open(log_file, "wb") as log_f:
            subprocess.Popen(
                ["python3", "-u", str(ROOT_DIR / "move-webserver.py")],
                cwd=ROOT_DIR,
                stdout=log_f,
                stderr=log_f,
                env=env,
            )
        log_msg("Starting the webserver...")

        new_pid = None
        for _ in range(10):
            if pid_file.exists():
                try:
                    new_pid = int(pid_file.read_text().strip())
                    break
                except Exception:
                    pass
            time.sleep(1)

        if not new_pid:
            log_msg("Error: PID file not created. Check logs:")
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as lf:
                    log_msg(lf.read())
            raise RuntimeError("Server failed to start")

        try:
            os.kill(new_pid, 0)
        except Exception:
            log_msg("Error: Server failed to start. Check logs:")
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as lf:
                    log_msg(lf.read())
            raise RuntimeError("Server failed to start")

        log_msg(f"Webserver restarted on port {port} with PID {new_pid}")


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
        changed = overlay_from_zip(content, ROOT_DIR)
    except Exception as exc:  # noqa: BLE001
        print(f"Error unpacking ZIP: {exc}", file=sys.stderr)
        return 1

    write_last_sha(latest_sha)
    print(f"Updated to {latest_sha}")
    if changed:
        install_requirements(ROOT_DIR)
    restart_webserver()
    return 0


if __name__ == "__main__":
    sys.exit(update())
