from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'templates_jinja' / 'set_inspector.html'
SCRIPT = Path(__file__).resolve().parents[1] / 'static' / 'webaudio-pianoroll.js'
INSPECTOR_JS = Path(__file__).resolve().parents[1] / 'static' / 'set_inspector.js'


def test_trig_modal_present():
    html = TEMPLATE.read_text()
    assert 'id="trigModal"' in html
    assert 'id="trig_select"' in html
    js = SCRIPT.read_text()
    assert 'data-action="trigcond"' in js
    inspector = INSPECTOR_JS.read_text()
    assert 'trigcondition' in inspector
