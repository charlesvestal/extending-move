import json
import copy
from typing import List, Dict, Any, Optional

from .euclidean import euclidean_rhythm


def create_euclid_clip(
    set_path: str,
    track_index: int,
    clip_index: int,
    pulses: List[int],
    rotates: List[int],
    reference_track: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a clip filled with Euclidean rhythms.

    The clip will be created on ``track_index``/``clip_index``. A template track
    is copied from ``reference_track`` (defaults to the previous track) so that
    devices and clip settings match. All existing notes in the new clip are
    removed before patterns are generated.
    """
    try:
        with open(set_path, "r") as f:
            song = json.load(f)

        tracks = song.get("tracks", [])
        if not tracks:
            return {"success": False, "message": "No tracks in set"}

        if reference_track is None:
            reference_track = max(0, track_index - 1)
        if reference_track < 0 or reference_track >= len(tracks):
            return {"success": False, "message": "Invalid reference track"}

        template_track = tracks[reference_track]
        # Ensure target track exists
        while len(tracks) <= track_index:
            tracks.append(copy.deepcopy(template_track))
        target_track = tracks[track_index] = copy.deepcopy(template_track)

        clip_slots = target_track.setdefault("clipSlots", [])
        template_slots = template_track.get("clipSlots", [])
        while len(clip_slots) <= clip_index:
            clip_slots.append({"hasStop": True, "clip": None})
        if clip_index < len(template_slots) and template_slots[clip_index].get("clip"):
            new_clip = copy.deepcopy(template_slots[clip_index]["clip"])
        else:
            # basic clip template
            new_clip = {
                "name": "Euclid",
                "color": target_track.get("color", 0),
                "isEnabled": True,
                "region": {"start": 0.0, "end": 4.0, "loop": {"start": 0.0, "end": 4.0, "isEnabled": True}},
                "notes": [],
                "envelopes": [],
            }
        new_clip["notes"] = []
        clip_slots[clip_index]["clip"] = new_clip

        grid = 0.25
        for i in range(16):
            steps = 16
            p = int(pulses[i]) if i < len(pulses) else 0
            r = int(rotates[i]) if i < len(rotates) else 0
            if p <= 0:
                continue
            ons = euclidean_rhythm(steps, p, r)
            note_num = 36 + i
            for step in ons:
                start = step * grid
                new_clip["notes"].append(
                    {
                        "noteNumber": note_num,
                        "startTime": start,
                        "duration": grid,
                        "velocity": 100,
                        "offVelocity": 0,
                    }
                )
        new_clip["notes"].sort(key=lambda x: x["startTime"])

        with open(set_path, "w") as f:
            json.dump(song, f, indent=2)

        return {"success": True, "message": "Euclidean clip created"}
    except Exception as e:
        return {"success": False, "message": f"Failed to create clip: {e}"}
