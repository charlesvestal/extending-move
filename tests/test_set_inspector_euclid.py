from pathlib import Path
from bs4 import BeautifulSoup

TEMPLATE = Path(__file__).resolve().parents[1] / 'templates_jinja' / 'set_inspector.html'
SCRIPT = Path(__file__).resolve().parents[1] / 'static' / 'webaudio-pianoroll.js'


def test_euclid_modal_present():
    html = TEMPLATE.read_text()
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.find(id='euclidModal') is not None
    js = SCRIPT.read_text()
    assert 'data-action="euclid"' in js
