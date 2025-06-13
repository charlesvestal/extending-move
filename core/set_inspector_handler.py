import json
import os
from typing import Any, Dict, List
from core.synth_preset_inspector_handler import (
    load_drift_schema,
    load_wavetable_schema,
    load_melodic_sampler_schema,
)

# Fallback ranges for well-known parameters
DEFAULT_RANGE: Dict[str, Dict[str, float]] = {
    "Voice_Transpose": {"min": -48, "max": 48},
    "Voice_Filter_Frequency": {"min": 20, "max": 20000},
}


def _scan_device(
    device: Dict[str, Any],
    param_meta: Dict[int, Dict[str, Any]],
    context: Dict[str, Any] | None = None,
) -> None:
    """Recursively scan a device collecting parameter metadata."""
    ctx = {**(context or {}), "deviceName": device.get("name")}

    for p_name, definition in device.get("parameters", {}).items():
        if isinstance(definition, dict) and isinstance(definition.get("id"), int):
            pid = definition["id"]
            r_min = definition.get("rangeMin")
            r_max = definition.get("rangeMax")
            if r_min is None or r_max is None:
                defaults = DEFAULT_RANGE.get(p_name)
                if defaults:
                    r_min = defaults.get("min") if r_min is None else r_min
                    r_max = defaults.get("max") if r_max is None else r_max
            param_meta[pid] = {
                "id": pid,
                "name": p_name,
                "deviceName": ctx.get("deviceName"),
                "padName": ctx.get("padName"),
                "rangeMin": r_min,
                "rangeMax": r_max,
            }

    if device.get("kind") in {"drumRack", "instrumentRack"}:
        for idx, chain in enumerate(device.get("chains", [])):
            sub_ctx = ctx.copy()
            if device.get("kind") == "drumRack":
                sub_ctx["padName"] = f"Pad{idx + 1}"
            for sub in chain.get("devices", []):
                _scan_device(sub, param_meta, sub_ctx)




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
        track_name = track_obj.get("name") or f"Track {track + 1}"
        clip_name = clip_obj.get("name") or f"Clip {clip + 1}"
        param_meta: Dict[int, Dict[str, Any]] = {}
        for dev in track_obj.get("devices", []):
            _scan_device(dev, param_meta)
        param_map: Dict[int, str] = {
            pid: (
                f"{meta['padName']}: {meta['name']}"
                if meta.get("padName")
                else f"{meta.get('deviceName')}: {meta['name']}"
            )
            for pid, meta in param_meta.items()
        }

        # Load parameter metadata from available instrument schemas
        schemas: Dict[str, Dict[str, Any]] = {}
        for loader in (load_drift_schema, load_wavetable_schema, load_melodic_sampler_schema):
            try:
                schemas.update(loader() or {})
            except Exception:
                pass

        param_ranges: Dict[int, Dict[str, float]] = {}
        for pid, meta in param_meta.items():
            info = schemas.get(meta["name"])
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

        # Patch envelope data with additional metadata
        patched_envs = []
        for env in envelopes:
            meta = param_meta.get(env.get("parameterId"))
            if meta:
                env = env.copy()
                if env.get("rangeMin") is None and meta.get("rangeMin") is not None:
                    env["rangeMin"] = meta["rangeMin"]
                if env.get("rangeMax") is None and meta.get("rangeMax") is not None:
                    env["rangeMax"] = meta["rangeMax"]
                env["owner"] = (
                    f"{meta['padName']}: {meta['name']}"
                    if meta.get("padName")
                    else f"{meta.get('deviceName')}: {meta['name']}"
                )
            patched_envs.append(env)
        return {
            "success": True,
            "message": "Clip loaded",
            "notes": notes,
            "envelopes": patched_envs,
            "region": region,
            "param_map": param_map,
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

        clip_obj = song["tracks"][track]["clipSlots"][clip]["clip"]
        envelopes = clip_obj.setdefault("envelopes", [])

        # Collect metadata for labeling and ranges
        param_meta: Dict[int, Dict[str, Any]] = {}
        for dev in song["tracks"][track].get("devices", []):
            _scan_device(dev, param_meta)
        meta = param_meta.get(parameter_id)

        env_data = {"parameterId": parameter_id, "breakpoints": breakpoints}
        if meta:
            if meta.get("rangeMin") is not None:
                env_data["rangeMin"] = meta["rangeMin"]
            if meta.get("rangeMax") is not None:
                env_data["rangeMax"] = meta["rangeMax"]
            env_data["owner"] = (
                f"{meta['padName']}: {meta['name']}" if meta.get("padName") else f"{meta.get('deviceName')}: {meta['name']}"
            )

        for env in envelopes:
            if env.get("parameterId") == parameter_id:
                env.update(env_data)
                break
        else:
            envelopes.append(env_data)

        with open(set_path, "w") as f:
            json.dump(song, f, indent=2)

        return {"success": True, "message": "Envelope saved"}
    except Exception as e:
        return {"success": False, "message": f"Failed to save envelope: {e}"}
