import json
import os
from typing import Any, Dict, List
import subprocess

def _get_xattr(path: str, attr: str) -> str:
    """Return extended attribute value or "Unknown"."""
    try:
        return (
            subprocess.check_output([
                "getfattr",
                "--only-values",
                "-n",
                attr,
                path,
            ], encoding="utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return "Unknown"


def get_set_pad_info(set_path: str) -> Dict[str, Any]:
    """Return pad index and color for the set if available."""
    try:
        parent = os.path.dirname(os.path.dirname(set_path))
        if not os.path.isdir(parent):
            return {"success": True, "pad": None, "color": None}

        pad = _get_xattr(parent, "user.song-index")
        color = _get_xattr(parent, "user.song-color")
        pad_val = int(pad) if pad.isdigit() else None
        color_val = int(color) if color.isdigit() else None
        return {"success": True, "pad": pad_val, "color": color_val}
    except Exception as e:
        return {"success": False, "message": f"Failed to read attributes: {e}"}


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
                    clips.append({"track": ti, "clip": ci, "name": name})
        return {"success": True, "message": "Clips loaded", "clips": clips}
    except Exception as e:
        return {"success": False, "message": f"Failed to read set: {e}"}


def get_clip_data(set_path: str, track: int, clip: int) -> Dict[str, Any]:
    """Return notes and envelopes for the specified clip."""
    try:
        with open(set_path, "r") as f:
            song = json.load(f)
        clip_obj = song["tracks"][track]["clipSlots"][clip]["clip"]
        notes = clip_obj.get("notes", [])
        envelopes = clip_obj.get("envelopes", [])
        region = clip_obj.get("region", {}).get("end", 4.0)
        return {
            "success": True,
            "message": "Clip loaded",
            "notes": notes,
            "envelopes": envelopes,
            "region": region,
        }
    except Exception as e:
        return {"success": False, "message": f"Failed to read clip: {e}"}


def build_clip_grid_html(clips: List[Dict[str, Any]], set_path: str) -> str:
    """Return HTML for a 4x8 clip grid."""
    grid: list[list[Dict[str, Any] | None]] = [[None for _ in range(8)] for _ in range(4)]
    for c in clips:
        ti = c.get("track")
        ci = c.get("clip")
        if 0 <= ti < 4 and 0 <= ci < 8:
            grid[ti][ci] = c

    html = '<div class="clip-grid">'
    for row in range(3, -1, -1):
        html += '<div class="clip-grid-row">'
        for col in range(8):
            clip = grid[row][col]
            if clip:
                val = f"{row}:{col}"
                name = clip.get("name", "")
                html += (
                    '<div class="clip-cell">'
                    f'<form method="post" action="/set-inspector">'
                    '<input type="hidden" name="action" value="show_clip">'
                    f'<input type="hidden" name="set_path" value="{set_path}">' \
                    f'<input type="hidden" name="clip_select" value="{val}">' \
                    f'<button type="submit">{name}</button>'
                    '</form></div>'
                )
            else:
                html += '<div class="clip-cell empty"></div>'
        html += '</div>'
    html += '</div>'
    return html
