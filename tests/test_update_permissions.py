import importlib.util
import io
import zipfile
import os
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "github_update",
    Path(__file__).resolve().parents[1] / "utility-scripts" / "github_update.py",
)
github_update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(github_update)

overlay_from_zip = github_update.overlay_from_zip


def _create_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        info = zipfile.ZipInfo("repo-main/bin/testfile")
        info.external_attr = 0o644 << 16
        zf.writestr(info, "test")
        zf.writestr("repo-main/requirements.txt", "")
    return buf.getvalue()


def test_bin_files_are_executable(tmp_path: Path) -> None:
    content = _create_zip()
    changed = overlay_from_zip(content, tmp_path)
    assert changed is True
    test_file = tmp_path / "bin" / "testfile"
    assert test_file.exists()
    assert os.access(test_file, os.X_OK), "file in bin should be executable"
