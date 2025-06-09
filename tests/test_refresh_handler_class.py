import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers.refresh_handler_class import RefreshHandler

class SimpleForm(dict):
    def getvalue(self, key, default=None):
        return self.get(key, default)


def test_refresh_handler_success(monkeypatch):
    h = RefreshHandler()
    form = SimpleForm(action="refresh_library")
    monkeypatch.setattr("handlers.refresh_handler_class.refresh_library", lambda: (True, "ok"))
    resp = h.handle_post(form)
    assert resp["message_type"] == "success"
    assert resp["message"] == "ok"


def test_refresh_handler_failure(monkeypatch):
    h = RefreshHandler()
    form = SimpleForm(action="refresh_library")
    monkeypatch.setattr("handlers.refresh_handler_class.refresh_library", lambda: (False, "bad"))
    resp = h.handle_post(form)
    assert resp["message_type"] == "error"
    assert "bad" in resp["message"]


def test_refresh_handler_bad_action():
    h = RefreshHandler()
    form = SimpleForm(action="wrong")
    resp = h.handle_post(form)
    assert resp["message_type"] == "error"
    assert "Invalid action" in resp["message"]


def test_refresh_handler_exception(monkeypatch):
    h = RefreshHandler()
    form = SimpleForm(action="refresh_library")
    def boom():
        raise RuntimeError("fail")
    monkeypatch.setattr("handlers.refresh_handler_class.refresh_library", boom)
    resp = h.handle_post(form)
    assert resp["message_type"] == "error"
    assert "fail" in resp["message"]
