from typing import List, Dict, Any

BASE_NOTE = 36
SEMI_UNIT = 170.6458282470703


def compute_overlay_notes(
    notes: List[Dict[str, Any]],
    selected_row: int,
    base_note: int = BASE_NOTE,
    semi_unit: float = SEMI_UNIT,
) -> List[Dict[str, float]]:
    """Return overlay notes for the given row using pitch-bend automation."""
    overlay: List[Dict[str, float]] = []
    if selected_row is None:
        return overlay
    for note in notes:
        if int(note.get("noteNumber", -1)) != int(selected_row):
            continue
        autom = note.get("automations") or {}
        pb = None
        if isinstance(autom, dict):
            pb = autom.get("PitchBend")
        if not pb:
            continue
        first = pb[0] if pb else None
        if not first:
            continue
        value = first.get("value")
        if value is None:
            continue
        try:
            semis = round(float(value) / semi_unit)
        except Exception:
            continue
        viz = base_note + semis
        if 0 <= viz <= 127:
            overlay.append({
                "noteNumber": viz,
                "startTime": float(note.get("startTime", 0.0)),
                "duration": float(note.get("duration", 0.0)),
            })
    return overlay
