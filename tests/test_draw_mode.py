from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'static' / 'webaudio-pianoroll.js'


def test_draw_mode_truncates_on_drumtracks():
    js = SCRIPT.read_text()
    assert 'delAreaNote(pt,this.grid,-1)' in js
    assert 'delAreaNote(px,this.grid,-1)' in js
