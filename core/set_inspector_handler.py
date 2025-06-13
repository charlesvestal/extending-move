import json
import os
from typing import Any, Dict, List
from core.synth_preset_inspector_handler import (
    load_drift_schema,
    load_wavetable_schema,
    load_melodic_sampler_schema,
)


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

        # Load parameter metadata from available instrument schemas
        schemas: Dict[str, Dict[str, Any]] = {}
        for loader in (load_drift_schema, load_wavetable_schema, load_melodic_sampler_schema):
            try:
                schemas.update(loader() or {})
            except Exception:
                pass

        param_ranges: Dict[int, Dict[str, float]] = {}
        for pid, name in param_map.items():
            info = schemas.get(name)
            if not info:
                continue
            min_v = info.get("min")
            max_v = info.get("max")
            if isinstance(min_v, (int, float)) and isinstance(max_v, (int, float)):
                param_ranges[pid] = {
                    "min": min_v,
                    "max": max_v,
                    "unit": info.get("unit"),
                }
        return {
            "success": True,
            "message": "Clip loaded",
            "notes": notes,
            "envelopes": envelopes,
            "region": region,
            "param_map": param_map,
            "param_ranges": param_ranges,
        }
    except Exception as e:
        return {"success": False, "message": f"Failed to read clip: {e}"}


def save_envelope(
    set_path: str,
    track: int,
    clip: int,
    parameter_id: int,
    breakpoints: List[Dict[str, float]],
) -> Dict[str, Any]:
    """Update or create an envelope and write the set back to disk."""
    try:
        with open(set_path, "r") as f:
            song = json.load(f)

        clip_obj = (
            song["tracks"][track]["clipSlots"][clip]["clip"]
        )
        envelopes = clip_obj.setdefault("envelopes", [])
        for env in envelopes:
            if env.get("parameterId") == parameter_id:
                env["breakpoints"] = breakpoints
                break
        else:
            envelopes.append({"parameterId": parameter_id, "breakpoints": breakpoints})

        with open(set_path, "w") as f:
            json.dump(song, f, indent=2)

        return {"success": True, "message": "Envelope saved"}
    except Exception as e:
        return {"success": False, "message": f"Failed to save envelope: {e}"}
