import json
import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.utils import load_set_template
from core.refresh_handler import refresh_library

class DummyProcError(Exception):
    pass


def test_load_set_template(tmp_path):
    tpl = {"x": 1}
    p = tmp_path / "set.json"
    p.write_text(json.dumps(tpl))
    result = load_set_template(str(p))
    assert result == tpl


def test_load_set_template_error(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{bad}")
    try:
        load_set_template(str(p))
    except Exception as e:
        assert "Failed to load template" in str(e)
    else:
        assert False, "Expected exception"


def test_refresh_library_success(monkeypatch):
    called = {}
    def fake_check(cmd, stderr=None):
        called['cmd'] = cmd
        return b''
    def fake_invalidate():
        called['inv'] = True
    monkeypatch.setattr('subprocess.check_output', fake_check)
    monkeypatch.setattr('core.refresh_handler.invalidate_cache', fake_invalidate)
    success, msg = refresh_library()
    assert success is True
    assert 'successfully' in msg
    assert called['cmd'][0] == 'dbus-send'
    assert called['inv'] is True


def test_refresh_library_failure(monkeypatch):
    class FakeError(Exception):
        output = b'bad'
    def fake_check(cmd, stderr=None):
        raise subprocess.CalledProcessError(1, cmd, output=b'bad')
    import subprocess
    monkeypatch.setattr(subprocess, 'check_output', fake_check)
    monkeypatch.setattr('core.refresh_handler.invalidate_cache', lambda: None)
    success, msg = refresh_library()
    assert not success
    assert 'Failed to refresh library' in msg

