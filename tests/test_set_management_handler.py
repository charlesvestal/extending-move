import sys
from pathlib import Path
import json
import mido

sys.path.append(str(Path(__file__).resolve().parents[1]))

import core.set_management_handler as sm
from handlers.set_management_handler_class import SetManagementHandler


def patch_output(monkeypatch, tmp_path):
    real_join = sm.os.path.join
    def fake_join(a, *p):
        if a == "/data/UserData/UserLibrary/Sets":
            return real_join(str(tmp_path), *p)
        return real_join(a, *p)
    monkeypatch.setattr(sm.os.path, "join", fake_join)
    monkeypatch.setattr(sm.os, "makedirs", lambda p, exist_ok=True: None)


def test_create_set(monkeypatch, tmp_path):
    patch_output(monkeypatch, tmp_path)
    result = sm.create_set("TestSet")
    assert result["success"]
    assert (tmp_path / "TestSet").exists()


def test_generate_c_major_chord_example(monkeypatch, tmp_path):
    patch_output(monkeypatch, tmp_path)
    monkeypatch.setattr(sm, "load_set_template", lambda p: {
        "tracks": [{"clipSlots": [{"clip": {"notes": [], "region": {"end": 0, "loop": {"end": 0}}}}]}],
        "tempo": 0
    })
    result = sm.generate_c_major_chord_example("ChordSet", tempo=90.0)
    assert result["success"]
    out = tmp_path / "ChordSet.abl"
    with open(out) as f:
        data = json.load(f)
    assert data["tempo"] == 90.0
    assert len(data["tracks"][0]["clipSlots"][0]["clip"]["notes"]) == 12


def test_generate_midi_set_from_file(monkeypatch, tmp_path):
    patch_output(monkeypatch, tmp_path)
    monkeypatch.setattr(sm, "load_set_template", lambda p: {
        "tracks": [{"clipSlots": [{"clip": {"notes": [], "region": {"end": 0, "loop": {"end": 0}}}}]}],
        "tempo": 0
    })
    midi_path = tmp_path / "x.mid"
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=100, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=480))
    mid.save(midi_path)
    result = sm.generate_midi_set_from_file("MidiSet", str(midi_path), tempo=110.0)
    assert result["success"]
    out = tmp_path / "MidiSet.abl"
    with open(out) as f:
        data = json.load(f)
    assert data["tempo"] == 110.0
    assert len(data["tracks"][0]["clipSlots"][0]["clip"]["notes"]) == 1


def test_generate_drum_set_from_file(monkeypatch, tmp_path):
    patch_output(monkeypatch, tmp_path)
    monkeypatch.setattr(sm, "load_set_template", lambda p: {
        "tracks": [{"clipSlots": [{"clip": {"notes": [], "region": {"end": 0, "loop": {"end": 0}}}}]}],
        "tempo": 0
    })
    midi_path = tmp_path / "d.mid"
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=36, velocity=100, time=0))
    track.append(mido.Message("note_off", note=36, velocity=0, time=240))
    mid.save(midi_path)
    result = sm.generate_drum_set_from_file("DrumSet", str(midi_path), tempo=120.0)
    assert result["success"]
    out = tmp_path / "DrumSet.abl"
    with open(out) as f:
        data = json.load(f)
    assert data["tempo"] == 120.0
    assert len(data["tracks"][0]["clipSlots"][0]["clip"]["notes"]) == 1
    assert data["tracks"][0]["clipSlots"][0]["clip"]["notes"][0]["noteNumber"] == 36


MINIMAL_TEMPLATE = {
    "tracks": [
        {"clipSlots": [{"clip": {
            "isPlaying": True, "name": "", "color": 1, "isEnabled": True,
            "region": {"start": 0.0, "end": 4.0, "loop": {"start": 0.0, "end": 4.0, "isEnabled": True}},
            "grooveId": 1, "notes": [], "stepEditorScrollPosition": 0.0, "envelopes": []
        }}, {"clip": None}]},
        {"clipSlots": [{"clip": None}, {"clip": None}]},
        {"clipSlots": [{"clip": None}, {"clip": None}]},
        {"clipSlots": [{"clip": None}, {"clip": None}]},
    ],
    "tempo": 120.0
}


def _make_midi(path, ticks_per_beat=480, note=60, duration_ticks=480):
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=note, velocity=80, time=0))
    track.append(mido.Message("note_off", note=note, velocity=0, time=duration_ticks))
    mid.save(path)


def test_assign_midi_to_track_new_set(monkeypatch, tmp_path):
    """New set created with correct clip structure."""
    patch_output(monkeypatch, tmp_path)
    import copy
    monkeypatch.setattr(sm, "load_set_template", lambda p: copy.deepcopy(MINIMAL_TEMPLATE))

    midi_path = tmp_path / "a.mid"
    _make_midi(midi_path)

    result = sm.assign_midi_to_track("MySet", str(midi_path), target_track=1, clip_color=3)
    assert result["success"], result["message"]

    out = tmp_path / "MySet.abl"
    with open(out) as f:
        data = json.load(f)

    clip = data["tracks"][0]["clipSlots"][0]["clip"]
    assert clip is not None
    assert clip["isPlaying"] is True
    assert "color" in clip
    assert clip["color"] == 3
    assert len(clip["notes"]) == 1
    assert clip["notes"][0]["noteNumber"] == 60


def test_assign_midi_to_track_clip_length_exact_bar(monkeypatch, tmp_path):
    """clip_length must not overshoot when max_end_time is exactly on a bar boundary."""
    patch_output(monkeypatch, tmp_path)
    import copy
    monkeypatch.setattr(sm, "load_set_template", lambda p: copy.deepcopy(MINIMAL_TEMPLATE))

    # 480 ticks/beat * 4 beats = 1 bar exactly (4.0 beats)
    midi_path = tmp_path / "exact.mid"
    _make_midi(midi_path, ticks_per_beat=480, duration_ticks=480 * 4)

    result = sm.assign_midi_to_track("ExactBarSet", str(midi_path), target_track=1, clip_color=1)
    assert result["success"], result["message"]

    out = tmp_path / "ExactBarSet.abl"
    with open(out) as f:
        data = json.load(f)

    clip = data["tracks"][0]["clipSlots"][0]["clip"]
    region_end = clip["region"]["end"]
    assert region_end == 4.0, f"Expected 4.0 beats, got {region_end}"
    assert clip["region"]["loop"]["end"] == region_end


def test_assign_midi_to_track_existing_set(monkeypatch, tmp_path):
    """Adding MIDI to an existing set updates the correct track slot."""
    patch_output(monkeypatch, tmp_path)
    import copy

    existing_set_path = tmp_path / "existing.abl"
    existing_data = copy.deepcopy(MINIMAL_TEMPLATE)
    with open(existing_set_path, "w") as f:
        json.dump(existing_data, f)

    midi_path = tmp_path / "b.mid"
    _make_midi(midi_path, note=48)

    result = sm.assign_midi_to_track(
        "existing", str(midi_path), target_track=2,
        existing_set_path=str(existing_set_path), clip_color=5
    )
    assert result["success"], result["message"]

    with open(existing_set_path) as f:
        data = json.load(f)

    clip = data["tracks"][1]["clipSlots"][0]["clip"]
    assert clip is not None
    assert clip["notes"][0]["noteNumber"] == 48
    assert clip["color"] == 5
    assert data["tempo"] == 120.0


def test_assign_midi_to_track_default_color(monkeypatch, tmp_path):
    """clip color defaults to 1 when clip_color is None."""
    patch_output(monkeypatch, tmp_path)
    import copy
    monkeypatch.setattr(sm, "load_set_template", lambda p: copy.deepcopy(MINIMAL_TEMPLATE))

    midi_path = tmp_path / "c.mid"
    _make_midi(midi_path)

    result = sm.assign_midi_to_track("DefaultColorSet", str(midi_path), target_track=1, clip_color=None)
    assert result["success"], result["message"]

    out = tmp_path / "DefaultColorSet.abl"
    with open(out) as f:
        data = json.load(f)

    clip = data["tracks"][0]["clipSlots"][0]["clip"]
    assert clip["color"] == 1


def test_assign_midi_to_track_invalid_track(monkeypatch, tmp_path):
    """Invalid track number returns failure."""
    midi_path = tmp_path / "e.mid"
    _make_midi(midi_path)

    result = sm.assign_midi_to_track("BadTrack", str(midi_path), target_track=5)
    assert not result["success"]
    assert "Invalid track number" in result["message"]


def test_sanitize_set_name_rejects_traversal():
    """Path traversal attempts in set_name are rejected."""
    assert sm.sanitize_set_name("../../../etc/passwd") is None
    assert sm.sanitize_set_name("..") is None
    assert sm.sanitize_set_name("foo/bar") is None
    assert sm.sanitize_set_name("foo\\bar") is None
    assert sm.sanitize_set_name("") is None
    assert sm.sanitize_set_name(None) is None
    # Valid names pass through
    assert sm.sanitize_set_name("My Set") == "My Set"
    assert sm.sanitize_set_name("Set-123") == "Set-123"


def test_assign_midi_to_track_rejects_traversal(monkeypatch, tmp_path):
    """Path traversal in set_name is rejected before any file operations."""
    midi_path = tmp_path / "trav.mid"
    _make_midi(midi_path)

    result = sm.assign_midi_to_track("../../../etc/evil", str(midi_path), target_track=1)
    assert not result["success"]
    assert "Invalid set name" in result["message"]


def test_generate_drum_set_from_file_rejects_traversal(monkeypatch, tmp_path):
    """Path traversal in set_name is rejected for drum import."""
    midi_path = tmp_path / "d.mid"
    _make_midi(midi_path)

    result = sm.generate_drum_set_from_file("../../evil", str(midi_path), tempo=120.0)
    assert not result["success"]
    assert "Invalid set name" in result["message"]


class _FakeFileItem:
    def __init__(self, filename, data=b"data"):
        self.filename = filename
        self.file = __import__("io").BytesIO(data)


class _FakeForm(dict):
    def getvalue(self, key, default=None):
        return self.get(key, default)


def test_existing_set_uuid_not_found_errors(monkeypatch):
    """When UUID is not found for an existing set, handler returns a clear error."""
    handler = SetManagementHandler()

    # Mock list_msets to return sets that don't match the requested name
    monkeypatch.setattr(
        "handlers.set_management_handler_class.list_msets",
        lambda return_free_ids=False: ([], {"used": set(), "free": list(range(32))})
    )

    form = _FakeForm()
    form["action"] = "upload_midi"
    form["midi_type"] = "melodic"
    form["set_mode"] = "existing"
    form["existing_set_name"] = "Nonexistent Set"
    form["midi_files"] = _FakeFileItem("test.mid")

    result = handler.handle_post(form)
    assert result["message_type"] == "error"
    assert "Could not find" in result["message"]


def test_partial_failure_reports_error(monkeypatch, tmp_path):
    """When some files in a batch fail, result is success:False with details."""
    handler = SetManagementHandler()

    monkeypatch.setattr(
        "handlers.set_management_handler_class.list_msets",
        lambda return_free_ids=False: ([], {"used": set(), "free": list(range(32))})
    )

    # Mock save_uploaded_file to return temp paths
    monkeypatch.setattr(handler, "save_uploaded_file", lambda f: (True, str(tmp_path / f.filename), None))
    monkeypatch.setattr(handler, "cleanup_upload", lambda p: None)

    # Mock assign_midi_to_track: first call succeeds, second fails
    call_count = [0]
    def fake_assign(set_name, midi_path, target_track, existing_path, tempo, clip_color):
        call_count[0] += 1
        if call_count[0] == 1:
            return {"success": True, "message": "ok", "path": str(tmp_path / "out.abl")}
        return {"success": False, "message": "Track 2 has no empty clip slots"}

    monkeypatch.setattr("handlers.set_management_handler_class.assign_midi_to_track", fake_assign)

    # Create temp files so save_uploaded_file's returned paths exist
    (tmp_path / "a.mid").write_bytes(b"data")
    (tmp_path / "b.mid").write_bytes(b"data")

    form = _FakeForm()
    form["action"] = "upload_midi"
    form["midi_type"] = "melodic"
    form["set_mode"] = "new"
    form["set_name"] = "TestSet"
    form["pad_color"] = "1"
    form["track_0"] = "1"
    form["track_1"] = "2"
    form["midi_files"] = [_FakeFileItem("a.mid"), _FakeFileItem("b.mid")]

    result = handler.handle_post(form)
    assert result["message_type"] == "error"
    assert "Partial failure" in result["message"]
    assert "a.mid" in result["message"]
    assert "b.mid" in result["message"]


def test_new_set_restore_calls_refresh_library(monkeypatch, tmp_path):
    """After successful new set restore, refresh_library() should be called."""
    handler = SetManagementHandler()

    monkeypatch.setattr(
        "handlers.set_management_handler_class.list_msets",
        lambda return_free_ids=False: ([], {"used": set(), "free": list(range(32))})
    )

    monkeypatch.setattr(handler, "save_uploaded_file", lambda f: (True, str(tmp_path / f.filename), None))
    monkeypatch.setattr(handler, "cleanup_upload", lambda p: None)

    # Mock assign_midi_to_track to succeed
    monkeypatch.setattr(
        "handlers.set_management_handler_class.assign_midi_to_track",
        lambda *a, **kw: {"success": True, "message": "ok", "path": str(tmp_path / "out.abl")}
    )

    # Create the .abl file so bundling can copy it
    (tmp_path / "out.abl").write_text("{}")

    # Mock restore_ablbundle to succeed
    monkeypatch.setattr(
        "handlers.set_management_handler_class.restore_ablbundle",
        lambda *a, **kw: {"success": True, "message": "Restored"}
    )

    # Track refresh_library calls
    refresh_called = [False]
    def track_refresh():
        refresh_called[0] = True
    monkeypatch.setattr("handlers.set_management_handler_class.refresh_library", track_refresh)

    (tmp_path / "test.mid").write_bytes(b"data")

    form = _FakeForm()
    form["action"] = "upload_midi"
    form["midi_type"] = "melodic"
    form["set_mode"] = "new"
    form["set_name"] = "TestSet"
    form["pad_index"] = "1"
    form["pad_color"] = "1"
    form["track_0"] = "1"
    form["midi_files"] = [_FakeFileItem("test.mid")]

    result = handler.handle_post(form)
    assert result["message_type"] == "success"
    assert refresh_called[0], "refresh_library() was not called after new set restore"

