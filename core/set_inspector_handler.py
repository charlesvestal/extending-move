import json
import os
from typing import Any, Dict, List


def _collect_param_ids(obj: Any, mapping: Dict[int, str]) -> None:
    """Recursively collect parameterId mappings from the given object."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, dict) and "id" in val and isinstance(val["id"], int):
                mapping[val["id"]] = val.get("customName") or key
            _collect_param_ids(val, mapping)
    elif isinstance(obj, list):
        for item in obj:
            _collect_param_ids(item, mapping)


def list_clips(set_path: str) -> Dict[str, Any]:
    """Return list of clips in the set."""
    try:
        with open(set_path, "r") as f:
            song = json.load(f)
        clips = []
        tracks = song.get("tracks", [])
        for ti, track in enumerate(tracks):
            for ci, slot in enumerate(track.get("clipSlots", [])):
                clip = slot.get("clip")
                if clip:
                    name = clip.get("name", f"Track {ti+1} Clip {ci+1}")
                    color = clip.get("color")
                    clips.append({"track": ti, "clip": ci, "name": name, "color": color})
        return {"success": True, "message": "Clips loaded", "clips": clips}
    except Exception as e:
        return {"success": False, "message": f"Failed to read set: {e}"}


def get_clip_data(set_path: str, track: int, clip: int) -> Dict[str, Any]:
    """Return notes and envelopes for the specified clip."""
    try:
        with open(set_path, "r") as f:
            song = json.load(f)
        track_obj = song["tracks"][track]
        clip_obj = track_obj["clipSlots"][clip]["clip"]
        notes = clip_obj.get("notes", [])
        envelopes = clip_obj.get("envelopes", [])
        region = clip_obj.get("region", {}).get("end", 4.0)
        param_map: Dict[int, str] = {}
        _collect_param_ids(track_obj.get("devices", []), param_map)
        return {
            "success": True,
            "message": "Clip loaded",
            "notes": notes,
            "envelopes": envelopes,
            "region": region,
            "param_map": param_map,
        }
    except Exception as e:
        return {"success": False, "message": f"Failed to read clip: {e}"}
