import json
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.file_browser import _list_directory, _check_json_file, _has_kind


def test_list_directory_cache(tmp_path):
    # create directory structure
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("x")
    dirs, files = _list_directory(str(tmp_path), "")
    assert dirs == ["sub"]
    assert "a.txt" in files

    # add new file to invalidate cache
    (tmp_path / "b.txt").write_text("y")
    dirs2, files2 = _list_directory(str(tmp_path), "")
    assert "b.txt" in files2


def test_list_directory_missing(tmp_path):
    missing = tmp_path / "missing"
    dirs, files = _list_directory(str(missing), "")
    assert dirs == [] and files == []


def test_check_json_file_caching(tmp_path, monkeypatch):
    p = tmp_path / "preset.json"
    p.write_text(json.dumps({"kind": "drift"}))
    assert _check_json_file(str(p), "drift") is True

    # patch json.load to ensure it isn't called when cached
    def fail_load(f):
        raise AssertionError("json.load called")
    monkeypatch.setattr("core.file_browser.json.load", fail_load)
    assert _check_json_file(str(p), "drift") is True

    # updating the file should trigger a reload
    monkeypatch.setattr("core.file_browser.json.load", lambda f: {})
    p.write_text("{}")
    import time
    time.sleep(0.01)
    os.utime(p, None)
    assert _check_json_file(str(p), "drift") is False


def test_check_json_file_missing(tmp_path):
    missing = tmp_path / "nope.json"
    assert _check_json_file(str(missing), "drift") is False


def test_has_kind_nested():
    data = {"x": [{"kind": "drift"}, {"y": {"kind": "other"}}]}
    assert _has_kind(data, "drift") is True
    assert _has_kind(data, "missing") is False
