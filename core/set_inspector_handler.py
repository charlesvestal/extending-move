import json
import os
from typing import Any, Dict, List
from core.synth_preset_inspector_handler import (
    load_drift_schema,
    load_wavetable_schema,
    load_melodic_sampler_schema,
)


def _collect_param_ids(
    obj: Any,
    mapping: Dict[int, str],
    context: Dict[int, str],
    prefix: str = "Track",
) -> None:
    """Recursively collect parameterId mappings with track/pad context."""
    if isinstance(obj, dict):
        if obj.get("kind") == "drumCell":
            pad_num = _collect_param_ids.pad_counter[0]
            _collect_param_ids.pad_counter[0] += 1
            prefix = f"Pad{pad_num}"
        for key, val in obj.items():
            if isinstance(val, dict) and "id" in val and isinstance(val["id"], int):
                mapping[val["id"]] = val.get("customName") or key
                context[val["id"]] = prefix
            _collect_param_ids(val, mapping, context, prefix)
    elif isinstance(obj, list):
        for item in obj:
            _collect_param_ids(item, mapping, context, prefix)


def _track_display_name(track_obj: Dict[str, Any], idx: int) -> str:
    """Return display name for a track using first device name."""
    devices = track_obj.get("devices", [])
    if devices and isinstance(devices, list):
        first = devices[0]
        if isinstance(first, dict) and first.get("name"):
            return first.get("name")
    return track_obj.get("name") or f"Track {idx + 1}"


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
        region_info = clip_obj.get("region", {})
        loop_info = region_info.get("loop", {})
        loop_start = loop_info.get("start", region_info.get("start", 0.0))
        loop_end = loop_info.get("end", region_info.get("end", 4.0))
        region = float(loop_end) - float(loop_start)
        track_name = _track_display_name(track_obj, track)
        clip_name = clip_obj.get("name") or f"Clip {clip + 1}"
        param_map: Dict[int, str] = {}
        param_context: Dict[int, str] = {}
        _collect_param_ids.pad_counter = [1]
        _collect_param_ids(track_obj.get("devices", []), param_map, param_context)

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
                    "min": float(min_v),
                    "max": float(max_v),
                    "unit": info.get("unit"),
                }

        # Attach range and domain info to envelopes
        for env in envelopes:
            pid = env.get("parameterId") or env.get("parameterIdName")
            if pid in param_ranges:
                env["rangeMin"] = param_ranges[pid]["min"]
                env["rangeMax"] = param_ranges[pid]["max"]
                if param_ranges[pid].get("unit"):
                    env["unit"] = param_ranges[pid]["unit"]
            else:
                env["rangeMin"] = 0.0
                env["rangeMax"] = 1.0
            raw_vals = [bp.get("value", 0.0) for bp in env.get("breakpoints", [])]
            if raw_vals and any(v < 0.0 or v > 1.0 for v in raw_vals):
                env["domainMin"] = min(env["rangeMin"], min(raw_vals))
                env["domainMax"] = max(env["rangeMax"], max(raw_vals))
            else:
                env["domainMin"] = env["rangeMin"]
                env["domainMax"] = env["rangeMax"]
        return {
            "success": True,
            "message": "Clip loaded",
            "notes": notes,
            "envelopes": envelopes,
            "region": region,
            "loop_start": loop_start,
            "param_map": param_map,
            "param_context": param_context,
            "param_ranges": param_ranges,
            "track_name": track_name,
            "clip_name": clip_name,
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
