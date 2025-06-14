import json
from typing import Any, Dict, List
from .utils import midi_to_note_name

SEMITONE_VALUE = 170.6458282470703
BASE_NOTE = 36  # C2


def _load_song(set_path: str) -> Dict[str, Any]:
    with open(set_path, "r") as f:
        return json.load(f)


def _save_song(set_path: str, data: Dict[str, Any]) -> None:
    with open(set_path, "w") as f:
        json.dump(data, f, indent=2)


def pads_with_pitch(notes: List[Dict[str, Any]]) -> Dict[int, bool]:
    """Return mapping of pad note numbers to whether they contain pitch bend."""
    result: Dict[int, bool] = {}
    for n in notes:
        pad = int(n.get("noteNumber", 0))
        has = bool(n.get("automations", {}).get("PitchBend"))
        result[pad] = result.get(pad, False) or has
    return result


def extract_pad_clip(set_path: str, track: int, clip: int, pad: int) -> Dict[str, Any]:
    """Return pitch-converted notes for a specific pad."""
    song = _load_song(set_path)
    clip_obj = song["tracks"][track]["clipSlots"][clip]["clip"]
    region_info = clip_obj.get("region", {})
    region_end = region_info.get("end", 4.0)
    loop_info = region_info.get("loop", {})
    loop_start = loop_info.get("start", 0.0)
    loop_end = loop_info.get("end", region_end)

    out_notes = []
    for n in clip_obj.get("notes", []):
        if int(n.get("noteNumber", 0)) != pad:
            continue
        pb = 0.0
        pb_list = n.get("automations", {}).get("PitchBend")
        if pb_list and isinstance(pb_list, list):
            pb = float(pb_list[0].get("value", 0.0))
        new_note = {
            "noteNumber": int(round(BASE_NOTE + pb / SEMITONE_VALUE)),
            "startTime": n.get("startTime", 0.0),
            "duration": n.get("duration", 0.0),
            "velocity": n.get("velocity", 1.0),
            "offVelocity": n.get("offVelocity", 0.0),
        }
        out_notes.append(new_note)

    track_name = song["tracks"][track].get("name")
    clip_name = clip_obj.get("name")

    return {
        "success": True,
        "notes": out_notes,
        "region": region_end,
        "loop_start": loop_start,
        "loop_end": loop_end,
        "track_name": track_name,
        "clip_name": clip_name,
    }


def save_pad_clip(
    set_path: str,
    track: int,
    clip: int,
    pad: int,
    notes: List[Dict[str, Any]],
    region_end: float,
    loop_start: float,
    loop_end: float,
) -> Dict[str, Any]:
    """Write edited pad notes back to the set."""
    song = _load_song(set_path)
    clip_obj = song["tracks"][track]["clipSlots"][clip]["clip"]
    other = [n for n in clip_obj.get("notes", []) if int(n.get("noteNumber", 0)) != pad]
    new_notes = []
    for n in notes:
        pb = (int(n.get("noteNumber", BASE_NOTE)) - BASE_NOTE) * SEMITONE_VALUE
        new_notes.append({
            "noteNumber": pad,
            "startTime": n.get("startTime", 0.0),
            "duration": n.get("duration", 0.0),
            "velocity": n.get("velocity", 1.0),
            "offVelocity": n.get("offVelocity", 0.0),
            "automations": {"PitchBend": [{"time": 0.0, "value": pb}]},
        })
    clip_obj["notes"] = sorted(other + new_notes, key=lambda x: x["startTime"])
    region = clip_obj.setdefault("region", {})
    region["start"] = 0.0
    region["end"] = region_end
    region["loop"] = {"start": loop_start, "end": loop_end}
    _save_song(set_path, song)
    return {"success": True, "message": "Pad clip saved"}
