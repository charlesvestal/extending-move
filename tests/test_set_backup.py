import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.set_backup_handler import backup_set, list_backups, restore_backup


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
    assert set_file.read_text() != "corrupt"
