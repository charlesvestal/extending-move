import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
import os
from datetime import datetime
from core.set_backup_handler import (
    BACKUP_EXT,
    backup_set,
    list_backups,
    restore_backup,
    get_current_timestamp,
    write_latest_timestamp,
)
from core.set_inspector_handler import save_clip, save_envelope


def create_simple_set(path):
    """Create a minimal Ableton set for saving tests."""
    clip = {
        "name": "Clip1",
        "notes": [],
        "envelopes": [],
        "region": {"end": 4.0},
    }
    track = {"name": "Track1", "devices": [], "clipSlots": [{"clip": clip}]}
    song = {"tracks": [track]}
    Path(path).write_text(json.dumps(song))


def test_backup_and_restore(tmp_path):
    set_file = tmp_path / "Song.abl"
    set_file.write_text("{\"tempo\":120}")
    # create multiple backups
    for i in range(11):
        set_file.write_text(f"version{i}")
        backup_set(str(set_file))
    backups = list_backups(str(set_file))
    assert len(backups) == 10
    latest = backups[0]['name']
    # corrupt file then restore
    set_file.write_text("corrupt")
    assert restore_backup(str(set_file), latest)
    restored_ts = latest.split(".")[-2]
    assert (set_file.parent / "backups" / "latest.txt").read_text().strip() == restored_ts
    assert set_file.read_text() != "corrupt"


def test_save_clip_and_envelope_create_backups(tmp_path):
    set_path = tmp_path / "Song.abl"
    create_simple_set(set_path)

    save_clip(str(set_path), 0, 0, [], [], None, 4.0, 0.0, 4.0)
    latest1 = (set_path.parent / "backups" / "latest.txt").read_text().strip()
    backups = list_backups(str(set_path))
    assert len(backups) == 1
    backup_ts1 = backups[0]['name'].split(".")[-2]
    assert backup_ts1 != latest1

    save_envelope(str(set_path), 0, 0, 1, [])
    latest2 = (set_path.parent / "backups" / "latest.txt").read_text().strip()
    backups = list_backups(str(set_path))
    assert len(backups) == 2
    backup_ts2 = backups[0]['name'].split(".")[-2]
    assert latest2 != backup_ts2
    assert latest1 != latest2


def test_get_current_timestamp(tmp_path):
    set_path = tmp_path / "Song.abl"
    create_simple_set(set_path)
    mtime_expected = datetime.fromtimestamp(os.path.getmtime(set_path)).strftime("%Y-%m-%d %H:%M:%S")
    assert get_current_timestamp(str(set_path)) == mtime_expected

    ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    write_latest_timestamp(str(set_path), ts)
    expected = datetime.strptime(ts, "%Y%m%dT%H%M%S%f").strftime("%Y-%m-%d %H:%M:%S")
    assert get_current_timestamp(str(set_path)) == expected
