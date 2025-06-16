from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'static' / 'webaudio-pianoroll.js'


def test_draw_mode_truncates_on_drumtracks():
    js = SCRIPT.read_text()
    # verify we do not remove notes across pitches
    assert 'delAreaNote(pt,this.grid,-1)' not in js
    assert 'delAreaNote(px,this.grid,-1)' not in js

    # ensure adding a note is not gated by a space check
    down_idx = js.index('editDrawDown')
    snippet = js[down_idx:down_idx + 200]
    assert 'if(ht.m=="s")' not in snippet
