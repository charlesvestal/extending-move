import sys
from pathlib import Path
import json
import mido

sys.path.append(str(Path(__file__).resolve().parents[1]))

import core.set_management_handler as sm


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

