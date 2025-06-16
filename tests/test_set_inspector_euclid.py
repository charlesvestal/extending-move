from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'templates_jinja' / 'set_inspector.html'
SCRIPT = Path(__file__).resolve().parents[1] / 'static' / 'webaudio-pianoroll.js'
INSPECTOR_JS = Path(__file__).resolve().parents[1] / 'static' / 'set_inspector.js'


def test_euclid_modal_present():
    html = TEMPLATE.read_text()
    assert 'id="euclidModal"' in html
    assert 'id="euclid_repeat"' in html
    js = SCRIPT.read_text()
    assert 'data-action="euclid"' in js
    assert 'kbimg.addEventListener(' in js
    assert 'wac-kb-highlight' in js
    inspector = INSPECTOR_JS.read_text()
    assert 'globalAlpha = 0.6' in inspector
    assert 'piano.editmode = defaultEditMode' in inspector


def test_shift_click_selection():
    js = SCRIPT.read_text()
    assert 'shiftSelect' in js
