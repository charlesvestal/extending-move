import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import set_inspector_handler as sih


def test_collect_param_ids_and_track_display():
    devices = [
        {"kind": "drumCell", "Gain": {"id": 1}},
        {"kind": "drift", "parameters": {"Vol": {"id": 2, "customName": "Volume"}}},
    ]
    mapping = {}
    ctx = {}
    sih._collect_param_ids.pad_counter = [1]
    sih._collect_param_ids(devices, mapping, ctx)
    assert mapping[1] == "Gain" and ctx[1] == "Pad1"
    assert mapping[2] == "Volume" and ctx[2] == "Track"

    track = {"name": "My Track", "devices": [{"name": "FirstDevice"}]}
    assert sih._track_display_name(track, 0) == "FirstDevice"
    assert sih._track_display_name({}, 1) == "Track 2"


def test_contains_drum_rack():
    track = {"devices": [{"kind": "drumRack", "chains": []}]}
    assert sih._contains_drum_rack(track)
    assert not sih._contains_drum_rack({"devices": [{"kind": "drift"}]})
