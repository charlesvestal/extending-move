import io
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "move_webserver",
    Path(__file__).resolve().parents[1] / "move-webserver.py",
)
move_webserver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(move_webserver)
import pytest

@pytest.fixture

def client(monkeypatch):
    move_webserver.app.config['TESTING'] = True
    return move_webserver.app.test_client()

def test_reverse_get(client, monkeypatch):
    monkeypatch.setattr(move_webserver, 'get_wav_files', lambda d: ['sample.wav'])
    resp = client.get('/reverse')
    assert resp.status_code == 200
    assert b'sample.wav' in resp.data

def test_reverse_post(client, monkeypatch):
    def fake_handle_post(form):
        return {'message': 'ok', 'message_type': 'success'}
    monkeypatch.setattr(move_webserver.reverse_handler, 'handle_post', fake_handle_post)
    resp = client.post('/reverse', data={'action': 'reverse_file', 'wav_file': 'sample.wav'})
    assert resp.status_code == 200
    assert b'ok' in resp.data

def test_restore_get(client, monkeypatch):
    def fake_get():
        return {'options': '<option value="1">1</option>', 'message': ''}
    monkeypatch.setattr(move_webserver.restore_handler, 'handle_get', fake_get)
    resp = client.get('/restore')
    assert resp.status_code == 200
    assert b'<option value="1">1</option>' in resp.data

def test_restore_post(client, monkeypatch):
    def fake_handle_post(form):
        return {'message': 'restored', 'message_type': 'success'}
    monkeypatch.setattr(move_webserver.restore_handler, 'handle_post', fake_handle_post)
    data = {
        'action': 'restore_ablbundle',
        'mset_index': '1',
        'mset_color': '1'
    }
    resp = client.post('/restore', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert b'restored' in resp.data

def test_slice_post(client, monkeypatch):
    def fake_handle_post(form):
        return {'message': 'sliced', 'message_type': 'success'}
    monkeypatch.setattr(move_webserver.slice_handler, 'handle_post', fake_handle_post)
    f = (io.BytesIO(b'data'), 'test.wav')
    data = {
        'action': 'slice',
        'mode': 'auto_place',
        'file': f
    }
    resp = client.post('/slice', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert b'sliced' in resp.data

def test_synth_macros_get(client, monkeypatch):
    def fake_get():
        return {
            'message': 'choose',
            'message_type': 'info',
            'options': '<option value="p">p</option>',
            'macros_html': '',
            'selected_preset': None,
        }
    monkeypatch.setattr(move_webserver.synth_handler, 'handle_get', fake_get)
    resp = client.get('/synth-macros')
    assert resp.status_code == 200
    assert b'choose' in resp.data

def test_synth_macros_post(client, monkeypatch):
    def fake_post(form):
        return {
            'message': 'saved',
            'message_type': 'success',
            'options': '<option value="x" selected>Sub/preset (Drift)</option>',
            'macros_html': '<p>done</p>',
            'selected_preset': 'x',
        }
    monkeypatch.setattr(move_webserver.synth_handler, 'handle_post', fake_post)
    resp = client.post('/synth-macros', data={'action': 'select_preset'})
    assert resp.status_code == 200
    assert b'saved' in resp.data
    assert b'name="preset_select" value="x"' in resp.data
    assert b'id="preset_select"' in resp.data and b'disabled' in resp.data
    assert b'Choose Another Preset' in resp.data

def test_drum_rack_inspector_get(client, monkeypatch):
    def fake_get():
        return {
            'options': '<option value="1">P</option>',
            'message': '',
            'samples_html': ''
        }
    monkeypatch.setattr(move_webserver.drum_rack_handler, 'handle_get', fake_get)
    resp = client.get('/drum-rack-inspector')
    assert resp.status_code == 200
    assert b'<option value="1">P</option>' in resp.data

def test_drum_rack_inspector_post(client, monkeypatch):
    def fake_post(form):
        return {
            'message': 'ok',
            'message_type': 'success',
            'options': '<option value="1">P</option>',
            'samples_html': '<div>grid</div>'
        }
    monkeypatch.setattr(move_webserver.drum_rack_handler, 'handle_post', fake_post)
    resp = client.post('/drum-rack-inspector', data={'action':'select_preset', 'preset_select':'x'})
    assert resp.status_code == 200
    assert b'grid' in resp.data

def test_chord_get(client):
    resp = client.get('/chord')
    assert resp.status_code == 200
    assert b'Chord Kit Generator' in resp.data
    assert b'id="chordList"' in resp.data

def test_detect_transients(client, monkeypatch):
    def fake_detect(form):
        return {'content': '{"success": true}', 'status': 200, 'headers': [('Content-Type', 'application/json')]}
    monkeypatch.setattr(move_webserver.slice_handler, 'handle_detect_transients', fake_detect)
    f = (io.BytesIO(b'data'), 'test.wav')
    resp = client.post('/detect-transients', data={'file': f}, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.json['success'] is True


def test_midi_upload_get(client, monkeypatch):
    def fake_get():
        return {
            'pad_options': '<option value="1">1</option>',
            'pad_color_options': '<option value="1">1</option>'
        }
    monkeypatch.setattr(move_webserver.set_management_handler, 'handle_get', fake_get)
    resp = client.get('/midi-upload')
    assert resp.status_code == 200
    assert b'<option value="1">1</option>' in resp.data


def test_midi_upload_post(client, monkeypatch):
    def fake_post(form):
        return {
            'message': 'ok',
            'message_type': 'success',
            'pad_options': '<option value="2">2</option>',
            'pad_color_options': '<option value="1">1</option>'
        }
    monkeypatch.setattr(move_webserver.set_management_handler, 'handle_post', fake_post)
    f = (io.BytesIO(b'data'), 'test.mid')
    data = {
        'action': 'upload_midi',
        'midi_type': 'melodic',
        'set_name': 'MySet',
        'pad_index': '1',
        'pad_color': '1',
        'midi_file': f
    }
    resp = client.post('/midi-upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert b'ok' in resp.data

def test_place_files_post(client, monkeypatch):
    def fake_place(form):
        return {'message': 'placed', 'message_type': 'success'}
    monkeypatch.setattr(move_webserver.file_placer_handler, 'handle_post', fake_place)
    f = (io.BytesIO(b'data'), 'sample.zip')
    data = {'mode': 'zip', 'file': f, 'destination': '/tmp'}
    resp = client.post('/place-files', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.json['message'] == 'placed'


def test_refresh_post(client, monkeypatch):
    def fake_refresh(form):
        return {'message': 'refreshed', 'message_type': 'success'}
    monkeypatch.setattr(move_webserver.refresh_handler, 'handle_post', fake_refresh)
    resp = client.post('/refresh', data={'action': 'refresh_library'})
    assert resp.status_code == 200
    assert resp.json['message'] == 'refreshed'
