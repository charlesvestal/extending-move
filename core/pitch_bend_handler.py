import json
from typing import List, Dict, Any

from core.set_inspector_handler import get_clip_data

PITCH_UNIT = 170.6458282470703
BASE_NOTE = 36  # C2


def extract_pitch_segments(notes: List[Dict[str, Any]], pad_note: int,
                           unit: float = PITCH_UNIT,
                           base: int = BASE_NOTE) -> List[Dict[str, Any]]:
    """Convert pitch bend automation into note segments for display."""
    segments: List[Dict[str, Any]] = []
    for note in notes:
        if int(note.get("noteNumber", -1)) != pad_note:
            continue
        start = float(note.get("startTime", 0.0))
        duration = float(note.get("duration", 0.0))
        pb_list = note.get("automations", {}).get("PitchBend", [])
        pb_list = sorted(pb_list, key=lambda x: x.get("time", 0.0))
        # Ensure we cover entire note duration
        if not pb_list:
            pb_list = [{"time": 0.0, "value": 0.0}]
        if pb_list[-1].get("time", 0.0) < duration:
            pb_list.append({"time": duration, "value": pb_list[-1].get("value", 0.0)})
        prev_time = 0.0
        prev_val = pb_list[0].get("value", 0.0)
        for bp in pb_list[1:]:
            seg_start = start + prev_time
            seg_dur = bp.get("time", 0.0) - prev_time
            semi = int(round(prev_val / unit))
            note_num = base + semi
            segments.append({
                "noteNumber": note_num,
                "startTime": seg_start,
                "duration": seg_dur,
                "velocity": note.get("velocity", 1.0),
                "offVelocity": note.get("offVelocity", 0.0),
            })
            prev_time = bp.get("time", 0.0)
            prev_val = bp.get("value", 0.0)
    return segments


def get_pad_pitch_data(set_path: str, track: int, clip: int, pad_note: int) -> Dict[str, Any]:
    """Load a clip and return pitch bend note segments for a pad."""
    clip_data = get_clip_data(set_path, track, clip)
    if not clip_data.get("success"):
        return clip_data
    notes = clip_data.get("notes", [])
    segments = extract_pitch_segments(notes, pad_note)
    return {
        "success": True,
        "message": clip_data.get("message", ""),
        "segments": segments,
        "clip_name": clip_data.get("clip_name"),
        "track_name": clip_data.get("track_name"),
    }
