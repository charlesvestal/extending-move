import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import set_inspector_handler as sih

TEMPLATE = Path(__file__).resolve().parents[1] / 'templates_jinja' / 'set_inspector.html'
PIANOROLL_JS = Path(__file__).resolve().parents[1] / 'static' / 'webaudio-pianoroll.js'
INSPECTOR_JS = Path(__file__).resolve().parents[1] / 'static' / 'set_inspector.js'


def test_enforce_drum_mode_basic():
    notes = [
        {"noteNumber": 60, "startTime": 0.0, "duration": 1.0},
        {"noteNumber": 60, "startTime": 0.5, "duration": 1.0},
    ]
    sih.enforce_drum_mode(notes)
    assert abs(notes[0]["duration"] - 0.5) < 1e-6


def test_track_has_drum_rack():
    track = {
        "devices": [
            {
                "kind": "instrumentRack",
                "chains": [{"devices": [{"kind": "drumRack"}]}],
            }
        ]
    }
    assert sih.track_has_drum_rack(track)


def test_drum_mode_assets_present():
    html = TEMPLATE.read_text()
    assert '🥁 Drum Mode' in html
    assert 'data-drum-mode' in html
    js = PIANOROLL_JS.read_text()
    assert 'drummode' in js and 'enforceDrumMode' in js
    inspector = INSPECTOR_JS.read_text()
    assert 'dataset.drumMode' in inspector
    assert 'piano.drummode' in inspector
