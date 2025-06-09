import json
from pathlib import Path

from core import synth_preset_inspector_handler as spih


def create_wavetable_preset(path, sprite_uri1=None, sprite_uri2=None):
    preset = {
        "kind": "instrumentRack",
        "chains": [
            {
                "devices": [
                    {
                        "kind": "wavetable",
                        "spriteUri1": sprite_uri1 or spih.WAVETABLE_SPRITE_PREFIX + "Basic%20Shapes",
                        "spriteUri2": sprite_uri2 or spih.WAVETABLE_SPRITE_PREFIX + "Sines%201",
                    }
                ]
            }
        ]
    }
    Path(path).write_text(json.dumps(preset))


def test_sprite_uri_helpers():
    name = "Ring Mod"
    uri = spih.sprite_name_to_uri(name)
    assert uri == spih.WAVETABLE_SPRITE_PREFIX + "Ring%20Mod"
    assert spih.sprite_uri_to_name(uri) == name


def test_update_and_extract_sprites(tmp_path):
    p = tmp_path / "preset.json"
    create_wavetable_preset(p)

    res = spih.extract_wavetable_sprites(str(p))
    assert res["success"]
    assert res["sprite1"] == "Basic Shapes"
    assert res["sprite2"] == "Sines 1"

    res = spih.update_wavetable_sprites(str(p), "Oboe", "Ring Mod")
    assert res["success"], res.get("message")

    res = spih.extract_wavetable_sprites(str(p))
    assert res["sprite1"] == "Oboe"
    assert res["sprite2"] == "Ring Mod"

