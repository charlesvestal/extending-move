import importlib.util
from pathlib import Path
import sys
import types
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

spec = importlib.util.spec_from_file_location(
    "move_webserver", Path(__file__).resolve().parents[1] / "move-webserver.py"
)
move_webserver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(move_webserver)

import handlers.update_handler_class as updater

@pytest.fixture
def client():
    move_webserver.app.config["TESTING"] = True
    return move_webserver.app.test_client()


def test_restart_only(client, monkeypatch):
    popen_called = {}

    class DummyPopen:
        def __init__(self, *a, **k):
            popen_called["args"] = a
            popen_called["kwargs"] = k

    monkeypatch.setattr(updater.subprocess, "Popen", DummyPopen)

    resp = client.post("/update", data={"action": "restart_server"})
    assert resp.status_code == 200
    assert b"Restarting server" in resp.data
    assert popen_called
