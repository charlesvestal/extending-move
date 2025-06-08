import os
import json
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

# Ensure project root is on the path for namespace packages
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.reverse_handler import reverse_wav_file
from core.slice_handler import detect_transients
from core.file_browser import generate_dir_html
from core.time_stretch_handler import time_stretch_wav, get_rubberband_binary
from core.midi_pattern_generator import (
    generate_pattern_set,
    create_c_major_downbeats,
)
from core.synth_param_editor_handler import update_parameter_values


def test_reverse_wav_file(tmp_path):
    sr = 22050
    t = np.linspace(0, 1, sr, endpoint=False)
    data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    orig_path = tmp_path / "orig.wav"
    sf.write(orig_path, data, sr)

    success, message, new_path = reverse_wav_file(orig_path.name, tmp_path)
    assert success, message
    assert os.path.exists(new_path)
    reversed_data, _ = sf.read(new_path, dtype="float32")
    assert np.isclose(reversed_data[0], data[-1], atol=1e-3)
    assert np.isclose(reversed_data[-1], data[0], atol=1e-3)


def test_detect_transients(tmp_path):
    sr = 22050
    data = np.zeros(sr)
    data[int(0.1 * sr):int(0.1 * sr) + 100] = 1.0
    data[int(0.6 * sr):int(0.6 * sr) + 100] = 1.0
    wav_path = tmp_path / "impulses.wav"
    sf.write(wav_path, data, sr)

    regions = detect_transients(str(wav_path), max_slices=None, delta=0.2)
    assert len(regions) >= 2
    assert regions[0]['start'] <= regions[0]['end']


def test_generate_pattern_set(tmp_path):
    pattern = create_c_major_downbeats(1)

    result = generate_pattern_set("TestSet", pattern, output_dir=str(tmp_path))
    assert result['success'], result.get('message')
    output_path = os.path.join(tmp_path, "TestSet.abl")
    assert os.path.exists(output_path)
    with open(output_path) as f:
        data = json.load(f)
    assert isinstance(data, dict)



def test_generate_dir_html(tmp_path):
    # create directory tree
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.wav").write_text("x")
    (tmp_path / "b.txt").write_text("x")

    html = generate_dir_html(
        str(tmp_path),
        "",
        "/upload",
        "file",
        "select",
        filter_key="wav",
    )
    assert 'data-path="sub"' in html
    assert 'a.wav' in html
    assert 'b.txt' not in html


def test_time_stretch_wav(tmp_path, monkeypatch):
    sr = 22050
    t = np.linspace(0, 1, sr, endpoint=False)
    data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    inp = tmp_path / "src.wav"
    outp = tmp_path / "out.wav"
    sf.write(inp, data, sr)

    from core import time_stretch_handler
    monkeypatch.setattr(time_stretch_handler, "refresh_library", lambda: (True, "ok"))

    success, msg, path = time_stretch_wav(str(inp), 2.0, str(outp))
    assert success
    assert os.path.exists(path)
    stretched, sr2 = sf.read(path, dtype="float32")
    assert abs(len(stretched) / sr2 - 2.0) < 0.2


def test_get_rubberband_binary_exists():
    path = get_rubberband_binary()
    assert path.exists()


def test_update_parameter_values(tmp_path):
    src = Path("examples/Track Presets/Drift/Analog Shape.ablpreset")
    dest = tmp_path / "out.ablpreset"
    result = update_parameter_values(str(src), {"Oscillator1_Shape": "0.5"}, str(dest))
    assert result["success"], result.get("message")
    with open(dest, "rb") as f:
        data = f.read()
    assert data.endswith(b"\n")
    preset = json.loads(data)
    val = (
        preset["chains"][0]
        ["devices"][0]
        ["chains"][0]
        ["devices"][0]
        ["parameters"]["Oscillator1_Shape"]["value"]
    )
    assert abs(val - 0.5) < 1e-6


def test_save_preset_no_changes(tmp_path):
    """Saving a preset without modifying parameters should produce identical output."""
    src = Path("examples/Track Presets/Drift/Analog Shape.ablpreset")

    # Extract existing parameter values
    from core.synth_preset_inspector_handler import extract_parameter_values

    info = extract_parameter_values(str(src))
    assert info["success"], info.get("message")
    # Convert values to strings as the web editor would submit
    updates = {p["name"]: str(p["value"]) for p in info["parameters"]}

    dest = tmp_path / "saved.ablpreset"
    result = update_parameter_values(str(src), updates, str(dest))
    assert result["success"], result.get("message")

    with open(src, "rb") as f:
        original = f.read()
    with open(dest, "rb") as f:
        written = f.read()
    assert written == original
