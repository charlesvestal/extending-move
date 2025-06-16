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

    # cursor should use pencil in draw mode
    assert 'pencilsrc:' in js
    assert 'observer:\'updateCursor\'' in js
    assert '0 23, pointer' in js


def test_note_mode_overwrites_on_drag():
    js = SCRIPT.read_text()
    # overlapping notes should be truncated via truncateOverlaps
    assert 'delAreaNote(ev.t,ev.g,ii)' not in js
    assert 'truncateOverlaps();' in js
    assert 'applyOverlapRules(' in js
