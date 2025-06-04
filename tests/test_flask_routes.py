import io
import flask_app
import pytest

@pytest.fixture

def client(monkeypatch):
    flask_app.app.config['TESTING'] = True
    return flask_app.app.test_client()

def test_reverse_get(client, monkeypatch):
    monkeypatch.setattr(flask_app, 'get_wav_files', lambda d: ['sample.wav'])
    resp = client.get('/reverse')
    assert resp.status_code == 200
    assert b'sample.wav' in resp.data

def test_reverse_post(client, monkeypatch):
    def fake_handle_post(form):
        return {'message': 'ok', 'message_type': 'success'}
    monkeypatch.setattr(flask_app.reverse_handler, 'handle_post', fake_handle_post)
    resp = client.post('/reverse', data={'action': 'reverse_file', 'wav_file': 'sample.wav'})
    assert resp.status_code == 200
    assert b'ok' in resp.data

def test_restore_get(client, monkeypatch):
    def fake_get():
        return {'options': '<option value="1">1</option>', 'message': ''}
    monkeypatch.setattr(flask_app.restore_handler, 'handle_get', fake_get)
    resp = client.get('/restore')
    assert resp.status_code == 200
    assert b'<option value="1">1</option>' in resp.data

def test_restore_post(client, monkeypatch):
    def fake_handle_post(form):
        return {'message': 'restored', 'message_type': 'success'}
    monkeypatch.setattr(flask_app.restore_handler, 'handle_post', fake_handle_post)
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
    monkeypatch.setattr(flask_app.slice_handler, 'handle_post', fake_handle_post)
    f = (io.BytesIO(b'data'), 'test.wav')
    data = {
        'action': 'slice',
        'mode': 'auto_place',
        'file': f
    }
    resp = client.post('/slice', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert b'sliced' in resp.data

def test_chord_get(client):
    resp = client.get('/chord')
    assert resp.status_code == 200
    assert b'Chord Kit Generator' in resp.data
    assert b'id="chordList"' in resp.data

def test_detect_transients(client, monkeypatch):
    def fake_detect(form):
        return {'content': '{"success": true}', 'status': 200, 'headers': [('Content-Type', 'application/json')]}
    monkeypatch.setattr(flask_app.slice_handler, 'handle_detect_transients', fake_detect)
    f = (io.BytesIO(b'data'), 'test.wav')
    resp = client.post('/detect-transients', data={'file': f}, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.json['success'] is True
