import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import list_msets_handler as lmh


def test_list_msets_no_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(lmh, "MSETS_DIRECTORY", str(tmp_path / "missing"))
    result = lmh.list_msets()
    assert result == []
    msets, ids = lmh.list_msets(return_free_ids=True)
    assert msets == []
    assert set(ids["free"]) == set(range(32))


def test_list_msets_and_free(monkeypatch, tmp_path):
    monkeypatch.setattr(lmh, "MSETS_DIRECTORY", str(tmp_path))
    (tmp_path / "uuid1" / "SetA").mkdir(parents=True)
    (tmp_path / "uuid2" / "SetB").mkdir(parents=True)

    mapping = {
        ("uuid1", "user.song-index"): "0",
        ("uuid2", "user.song-index"): "31",
        ("uuid1", "user.song-color"): "1",
        ("uuid2", "user.song-color"): "2",
    }

    def fake_get_xattr(rel, attr):
        return mapping.get((rel, attr), "")

    monkeypatch.setattr(lmh, "get_xattr_value", fake_get_xattr)

    msets, ids = lmh.list_msets(return_free_ids=True)
    assert [m["mset_id"] for m in msets] == [0, 31]
    assert ids["used"] == {0, 31}
    free = lmh.list_msets_free()
    assert 0 not in free and 31 not in free
    assert len(free) == 30
