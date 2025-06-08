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

    # Adding a new file should invalidate the cache automatically
    (tmp_path / "new.wav").write_text("x")
    html2 = generate_dir_html(
        str(tmp_path),
        "",
        "/upload",
        "file",
        "select",
        filter_key="wav",
    )
    assert 'new.wav' in html2


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
    src = Path("examples/Track Presets/Drift/Analog Shape - Core.json")
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


def test_update_macro_values(tmp_path):
    src = Path("examples/Track Presets/Drift/Analog Shape - Core.json")
    dest = tmp_path / "out.ablpreset"
    from core.synth_param_editor_handler import update_macro_values
    result = update_macro_values(str(src), {0: "64.5"}, str(dest))
    assert result["success"], result.get("message")
    with open(dest, "rb") as f:
        data = f.read()
    assert data.endswith(b"\n")
    preset = json.loads(data)
    # Macro0 occurs in multiple places; ensure top-level updated
    assert abs(preset["parameters"]["Macro0"] - 64.5) < 1e-6


def test_save_preset_no_changes(tmp_path):
    """Saving a preset without modifying parameters should produce identical output."""
    src = Path("examples/Track Presets/Drift/Analog Shape - Core.json")

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


def test_macro_names_remain_default_without_custom_names():
    """Macros mapped without custom names should keep default labels."""
    src = Path("examples/Track Presets/Drift/Analog Shape - Core.json")
    from core.synth_preset_inspector_handler import extract_macro_information

    info = extract_macro_information(str(src))
    assert info["success"], info.get("message")

    names = {m["index"]: m["name"] for m in info["macros"]}

    # Macros with custom names should be preserved
    assert names[0] == "Filter Cutoff"
    assert names[1] == "Shape"
    assert names[4] == "Attack"
    assert names[5] == "DSR"
    assert names[6] == "Shape Decay"

    # Macros lacking a customName should keep their default titles
    assert names[2] == "Macro 2"
    assert names[3] == "Macro 3"
    assert names[7] == "Macro 7"


def test_extract_macro_info_adds_missing_macros(tmp_path):
    preset_path = tmp_path / "empty.ablpreset"
    preset = {
        "kind": "instrumentRack",
        "parameters": {"Enabled": True},
        "chains": [],
    }
    preset_path.write_text(json.dumps(preset))

    from core.synth_preset_inspector_handler import extract_macro_information

    info = extract_macro_information(str(preset_path))
    assert info["success"], info.get("message")
    assert len(info["macros"]) == 8
    # All macros should use default names
    assert all(m["name"] == f"Macro {m['index']}" for m in info["macros"])


def test_remove_macro_name(tmp_path):
    preset_src = Path("examples/Track Presets/Drift/Analog Shape - Core.json")
    preset_copy = tmp_path / "copy.ablpreset"
    preset_copy.write_text(preset_src.read_text())

    from core.synth_preset_inspector_handler import (
        extract_macro_information,
        update_preset_macro_names,
    )

    # Remove the name for Macro0
    result = update_preset_macro_names(str(preset_copy), {0: ""})
    assert result["success"], result.get("message")

    info = extract_macro_information(str(preset_copy))
    assert info["success"], info.get("message")

    names = {m["index"]: m["name"] for m in info["macros"]}
    assert names[0] == "Macro 0"
    assert names[1] == "Shape"

    with open(preset_copy) as f:
        data = json.load(f)
    assert "customName" not in data["chains"][0]["devices"][0]["parameters"]["Macro0"]

