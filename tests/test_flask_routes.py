import io
import importlib.util
from pathlib import Path
import sys
import numpy as np
import soundfile as sf

# Ensure project root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

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

def test_reverse_get(client):
    resp = client.get('/reverse')
    assert resp.status_code == 200
    assert b'class="file-browser"' in resp.data

def test_reverse_post(client, monkeypatch):
    def fake_handle_post(form):
        return {'message': 'ok', 'message_type': 'success'}
    monkeypatch.setattr(move_webserver.reverse_handler, 'handle_post', fake_handle_post)
    resp = client.post('/reverse', data={'action': 'reverse_file', 'wav_file': 'sample.wav'})
    assert resp.status_code == 200
    assert b'ok' in resp.data

def test_restore_get(client, monkeypatch):
    def fake_get():
        return {'options': '<option value="1">1</option>', 'pad_grid': '<div class="pad-grid"></div>', 'message': ''}
    monkeypatch.setattr(move_webserver.restore_handler, 'handle_get', fake_get)
    resp = client.get('/restore')
    assert resp.status_code == 200
    assert b'class="pad-grid"' in resp.data

def test_restore_post(client, monkeypatch):
    def fake_handle_post(form):
        return {'message': 'restored', 'message_type': 'success', 'pad_grid': '<div class="pad-grid"></div>', 'options': ''}
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
            'schema_json': '{}',
        }
    monkeypatch.setattr(move_webserver.synth_handler, 'handle_get', fake_get)
    resp = client.get('/synth-macros')
    assert resp.status_code == 200
    assert b'choose' in resp.data
    assert b'Currently loaded preset' not in resp.data

def test_synth_macros_post(client, monkeypatch):
    def fake_post(form):
        return {
            'message': 'saved',
            'message_type': 'success',
            'macros_html': '<p>done</p>',
            'all_params_html': '<ul></ul>',
            'selected_preset': 'x',
            'browser_root': '/tmp',
            'schema_json': '{}',
        }
    monkeypatch.setattr(move_webserver.synth_handler, 'handle_post', fake_post)
    resp = client.post('/synth-macros', data={'action': 'select_preset'})
    assert resp.status_code == 200
    assert b'saved' in resp.data
    assert b'Choose Another Preset' in resp.data
    assert b'<p>done</p>' in resp.data
    assert b'Currently loaded preset:' in resp.data
    assert b'View All Parameters' in resp.data

def test_synth_params_get(client, monkeypatch):
    from handlers.synth_param_editor_handler_class import DEFAULT_PRESET

    def fake_get():
        return {
            'message': 'pick',
            'message_type': 'info',
            'file_browser_html': '<ul></ul>',
            'params_html': '',
            'selected_preset': None,
            'param_count': 0,
            'browser_root': '/tmp',
            'default_preset_path': DEFAULT_PRESET,
        }
    monkeypatch.setattr(move_webserver.synth_param_handler, 'handle_get', fake_get)
    resp = client.get('/synth-params')
    assert resp.status_code == 200
    assert b'pick' in resp.data
    assert b'Editing:' not in resp.data
    assert b'Create New Drift Preset' in resp.data

def test_synth_params_post(client, monkeypatch):
    def fake_post(form):
        return {
            'message': 'done',
            'message_type': 'success',
            'params_html': '<div>p</div>',
            'browser_root': '/tmp',
            'selected_preset': 'x',
            'param_count': 1,
        }
    monkeypatch.setattr(move_webserver.synth_param_handler, 'handle_post', fake_post)
    resp = client.post('/synth-params', data={'action': 'select_preset'})
    assert resp.status_code == 200
    assert b'done' in resp.data
    assert b'Editing:' in resp.data
    assert b'<div>p</div>' in resp.data
    assert b'name="rename"' in resp.data
    assert b'name="new_preset_name"' in resp.data
    assert b'disabled' in resp.data

def test_synth_params_new_preset(client, monkeypatch):
    from handlers.synth_param_editor_handler_class import DEFAULT_PRESET

    def fake_post(form):
        return {
            'message': 'loaded',
            'message_type': 'success',
            'params_html': '<div>x</div>',
            'browser_root': '/tmp',
            'selected_preset': DEFAULT_PRESET,
            'param_count': 2,
            'default_preset_path': DEFAULT_PRESET,
        }
    monkeypatch.setattr(move_webserver.synth_param_handler, 'handle_post', fake_post)
    resp = client.post('/synth-params', data={'action': 'new_preset'})
    assert resp.status_code == 200
    assert b'loaded' in resp.data
    assert b'Editing:' in resp.data
    assert b'name="rename"' in resp.data
    assert b'name="new_preset_name"' in resp.data

def test_drum_rack_inspector_get(client, monkeypatch):
    def fake_get():
        return {
            'file_browser_html': '<ul></ul>',
            'message': '',
            'samples_html': '',
            'browser_root': '/tmp'
        }
    monkeypatch.setattr(move_webserver.drum_rack_handler, 'handle_get', fake_get)
    resp = client.get('/drum-rack-inspector')
    assert resp.status_code == 200
    assert b'class="file-browser"' in resp.data
    assert b'Currently loaded preset' not in resp.data

def test_drum_rack_inspector_post(client, monkeypatch):
    def fake_post(form):
        return {
            'message': 'ok',
            'message_type': 'success',
            'samples_html': '<div>grid</div>',
            'browser_root': '/tmp',
            'selected_preset': 'x',
        }
    monkeypatch.setattr(move_webserver.drum_rack_handler, 'handle_post', fake_post)
    resp = client.post('/drum-rack-inspector', data={'action':'select_preset', 'preset_select':'x'})
    assert resp.status_code == 200
    assert b'<div>grid</div>' in resp.data
    assert b'Currently loaded preset:' in resp.data

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
            'pad_color_options': '<option value="1">1</option>',
            'pad_grid': '<div class="pad-grid"></div>'
        }
    monkeypatch.setattr(move_webserver.set_management_handler, 'handle_get', fake_get)
    resp = client.get('/midi-upload')
    assert resp.status_code == 200
    assert b'class="pad-grid"' in resp.data


def test_midi_upload_post(client, monkeypatch):
    def fake_post(form):
        return {
            'message': 'ok',
            'message_type': 'success',
            'pad_options': '<option value="2">2</option>',
            'pad_color_options': '<option value="1">1</option>',
            'pad_grid': '<div class="pad-grid"></div>'
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


def test_refresh_get(client, monkeypatch):
    monkeypatch.setattr(move_webserver, 'refresh_library', lambda: (True, 'done'))
    resp = client.get('/refresh')
    assert resp.status_code == 200
    assert b'done' in resp.data

def test_index_redirect(client):
    resp = client.get('/')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/restore')


def test_browse_dir(client, tmp_path):
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'a.wav').write_text('x')
    (tmp_path / 'b.txt').write_text('x')
    query = {
        'root': str(tmp_path),
        'path': '',
        'action_url': '/do',
        'field_name': 'file',
        'action_value': 'act',
        'filter': 'wav',
    }
    resp = client.get('/browse-dir', query_string=query)
    assert resp.status_code == 200
    data = resp.data.decode()
    assert 'data-path="sub"' in data
    assert 'a.wav' in data
    assert 'b.txt' not in data


def test_samples_route(client, tmp_path, monkeypatch):
    sample = tmp_path / 's.wav'
    sample.write_bytes(b'data')
    real_join = move_webserver.os.path.join
    real_real = move_webserver.os.path.realpath

    base = '/data/UserData/UserLibrary/Samples/Preset Samples'

    def fake_join(a, *rest):
        if a == base:
            return real_join(tmp_path, *rest)
        return real_join(a, *rest)

    def fake_real(path):
        if path.startswith(base):
            new = path.replace(base, str(tmp_path), 1)
            return real_real(new)
        return real_real(path)

    monkeypatch.setattr(move_webserver.os.path, 'join', fake_join)
    monkeypatch.setattr(move_webserver.os.path, 'realpath', fake_real)
    resp = client.get(f'/samples/{sample.name}')
    assert resp.status_code == 200
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    assert b'data' in resp.data


def test_samples_route_not_found(client, tmp_path, monkeypatch):
    real_join = move_webserver.os.path.join
    real_real = move_webserver.os.path.realpath
    base = '/data/UserData/UserLibrary/Samples/Preset Samples'

    def fake_join(a, *rest):
        if a == base:
            return real_join(tmp_path, *rest)
        return real_join(a, *rest)

    def fake_real(path):
        if path.startswith(base):
            new = path.replace(base, str(tmp_path), 1)
            return real_real(new)
        return real_real(path)

    monkeypatch.setattr(move_webserver.os.path, 'join', fake_join)
    monkeypatch.setattr(move_webserver.os.path, 'realpath', fake_real)
    resp = client.get('/samples/missing.wav')
    assert resp.status_code == 404


def test_pitch_shift_route(client, monkeypatch):
    import sys
    monkeypatch.setattr(
        sys.modules['core.time_stretch_handler'],
        'pitch_shift_array',
        lambda d, sr, st: d,
    )
    sr = 22050
    t = np.linspace(0, 1, sr, endpoint=False)
    data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, data, sr, format='WAV')
    buf.seek(0)
    resp = client.post(
        '/pitch-shift',
        data={'semitones': '2', 'audio': (buf, 'test.wav')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 200
    shifted, sr2 = sf.read(io.BytesIO(resp.data), dtype='float32')
    assert sr2 == sr
    assert len(shifted) == len(data)


