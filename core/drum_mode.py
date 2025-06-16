from typing import List, Dict


def enforce_drum_mode(row_notes: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Enforce monophonic behavior on a list of notes for one pitch."""
    row_notes.sort(key=lambda n: n.get("startTime", 0))
    i = 0
    while i < len(row_notes) - 1:
        a = row_notes[i]
        b = row_notes[i + 1]
        a_start = float(a.get("startTime", 0))
        b_start = float(b.get("startTime", 0))
        a_end = a_start + float(a.get("duration", 0))
        if a_end > b_start:
            new_dur = b_start - a_start
            if new_dur <= 0:
                row_notes.pop(i)
                continue
            a["duration"] = new_dur
        i += 1
    return row_notes

