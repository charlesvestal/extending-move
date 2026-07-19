import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers.base_handler import BaseHandler

class DummyField:
    def __init__(self, filename, data):
        self.filename = filename
        self.file = io.BytesIO(data)

class DummyForm(dict):
    def getvalue(self, key, default=None):
        return self.get(key, default)


def test_validate_action_success():
    handler = BaseHandler()
    form = DummyForm(action="do")
    ok, err = handler.validate_action(form, "do")
    assert ok is True
    assert err is None


def test_validate_action_failure():
    handler = BaseHandler()
    form = DummyForm(action="bad")
    ok, err = handler.validate_action(form, "good")
    assert ok is False
    assert err["message_type"] == "error"
    assert "Invalid action" in err["message"]


def test_handle_file_upload_and_cleanup(tmp_path):
    handler = BaseHandler()
    handler.upload_dir = tmp_path
    form = DummyForm()
    form["file"] = DummyField("test.txt", b"abc")
    success, path, err = handler.handle_file_upload(form)
    assert success is True
    assert err is None
    assert Path(path).exists()
    with open(path, "rb") as f:
        assert f.read() == b"abc"
    handler.cleanup_upload(path)
    assert not Path(path).exists()


def test_format_responses():
    handler = BaseHandler()
    ok = handler.format_success_response("ok", extra=1)
    err = handler.format_error_response("bad")
    info = handler.format_info_response("info")
    assert ok["message"] == "ok" and ok["message_type"] == "success" and ok["extra"] == 1
    assert err["message_type"] == "error"
    assert info["message_type"] == "info"


def test_save_uploaded_file_unique_temp_names(tmp_path):
    """Two files with the same basename get different temp paths."""
    handler = BaseHandler()
    handler.upload_dir = str(tmp_path)

    f1 = DummyField("clip.mid", b"data1")
    f2 = DummyField("clip.mid", b"data2")

    ok1, path1, err1 = handler.save_uploaded_file(f1)
    ok2, path2, err2 = handler.save_uploaded_file(f2)

    assert ok1 and ok2
    assert err1 is None and err2 is None
    assert path1 != path2
    assert path1.endswith(".mid")
    assert path2.endswith(".mid")
    with open(path1, "rb") as f:
        assert f.read() == b"data1"
    with open(path2, "rb") as f:
        assert f.read() == b"data2"
    handler.cleanup_upload(path1)
    handler.cleanup_upload(path2)


def test_format_json_response():
    handler = BaseHandler()
    result = handler.format_json_response({"a": 1}, status=201)
    assert result["status"] == 201
    assert ("Content-Type", "application/json") in result["headers"]
    assert result["content"] == "{" + '"a": 1' + "}"

