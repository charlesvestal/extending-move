import json
import argparse
from typing import Any, Dict, Tuple

# Fallback ranges when metadata is missing
DEFAULT_RANGE = {
    "Voice_Transpose": (-48.0, 48.0),
    "Transpose": (-48.0, 48.0),
    "Filter_Frequency": (20.0, 20000.0),
    "Voice_Filter_Frequency": (20.0, 20000.0),
}

ParamMeta = Dict[str, Any]


def _add_meta(meta_by_id: Dict[int, ParamMeta], meta_by_name: Dict[str, ParamMeta], meta: ParamMeta) -> None:
    """Store parameter metadata keyed by id and name."""
    pid = meta.get("id")
    name = meta.get("name")
    if pid is not None:
        meta_by_id[pid] = meta
    if name and name not in meta_by_name:
        meta_by_name[name] = meta


def _scan_device(device: Dict[str, Any], context: Dict[str, Any], meta_by_id: Dict[int, ParamMeta], meta_by_name: Dict[str, ParamMeta]) -> None:
    """Recursively collect parameter metadata from a device."""
    device_name = device.get("name") or device.get("kind")
    ctx = {
        "deviceName": device_name,
        "padName": context.get("padName"),
    }

    for name, val in device.get("parameters", {}).items():
        pid = None
        rmin = None
        rmax = None
        if isinstance(val, dict):
            pid = val.get("id")
            mapping = val.get("macroMapping") or {}
            rmin = mapping.get("rangeMin") or val.get("rangeMin")
            rmax = mapping.get("rangeMax") or val.get("rangeMax")
        meta = {
            "id": pid,
            "name": name,
            "deviceName": device_name,
            "padName": ctx.get("padName"),
            "rangeMin": rmin,
            "rangeMax": rmax,
        }
        _add_meta(meta_by_id, meta_by_name, meta)

    for idx, chain in enumerate(device.get("chains", [])):
        if device.get("kind") == "drumRack":
            child_ctx = {"padName": f"Pad{idx+1}"}
        else:
            child_ctx = {"padName": ctx.get("padName")}
        for dev in chain.get("devices", []):
            _scan_device(dev, child_ctx, meta_by_id, meta_by_name)


def build_param_meta(track: Dict[str, Any]) -> Tuple[Dict[int, ParamMeta], Dict[str, ParamMeta]]:
    """Build parameter metadata lookup tables for a track."""
    meta_by_id: Dict[int, ParamMeta] = {}
    meta_by_name: Dict[str, ParamMeta] = {}
    for dev in track.get("devices", []):
        _scan_device(dev, {}, meta_by_id, meta_by_name)
    return meta_by_id, meta_by_name


def _default_range(name: str) -> Tuple[float, float]:
    return DEFAULT_RANGE.get(name, (0.0, 1.0))


def process_envelopes(clip: Dict[str, Any], meta_by_id: Dict[int, ParamMeta]) -> None:
    """Inject range info and convert breakpoint values in-place."""
    for env in clip.get("envelopes", []):
        pid = env.get("parameterId")
        meta = meta_by_id.get(pid)
        if not meta:
            continue
        name = meta.get("name")
        rmin = meta.get("rangeMin")
        rmax = meta.get("rangeMax")
        if rmin is None or rmax is None:
            rmin, rmax = _default_range(name)
        env.setdefault("rangeMin", rmin)
        env.setdefault("rangeMax", rmax)
        for bp in env.get("breakpoints", []):
            val = bp.get("value")
            if isinstance(val, (int, float)):
                bp["value"] = val * (env["rangeMax"] - env["rangeMin"]) + env["rangeMin"]
        env["owner"] = meta.get("padName") or meta.get("deviceName")


def process_set(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process all clips in the provided song/track JSON data."""
    for track in data.get("tracks", []):
        meta_by_id, _ = build_param_meta(track)
        for slot in track.get("clipSlots", []):
            clip = slot.get("clip")
            if clip:
                process_envelopes(clip, meta_by_id)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-process clip envelopes")
    parser.add_argument("input", help="Path to the JSON song/set file")
    parser.add_argument("output", nargs="?", help="Optional output path")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    processed = process_set(data)

    out_path = args.output or args.input
    with open(out_path, "w") as f:
        json.dump(processed, f, indent=2)


if __name__ == "__main__":
    main()
