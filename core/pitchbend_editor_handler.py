#!/usr/bin/env python3
"""Utilities for editing drum pad pitchbend notes."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PITCHBEND_STEP = 170.6458282470703
C2_NOTE = 48


def pitchbend_to_note_pitch(pb_value: float) -> float:
    """Convert a pitchbend value to a note pitch number."""
    return C2_NOTE + pb_value / PITCHBEND_STEP


def note_pitch_to_pitchbend(pitch: float) -> float:
    """Convert a note pitch back to a pitchbend value."""
    return (pitch - C2_NOTE) * PITCHBEND_STEP


def get_pad_notes(notes: List[Dict[str, Any]], pad_number: int) -> List[Dict[str, Any]]:
    """Return notes for the given pad with derived pitch information."""
    pad_notes = []
    for note in notes:
        if note.get("noteNumber") != pad_number:
            continue
        pb_value = 0.0
        autom = note.get("automations", {})
        if autom and autom.get("PitchBend"):
            pb_value = autom["PitchBend"][0].get("value", 0.0)
        pad_notes.append(
            {
                "startTime": note.get("startTime"),
                "duration": note.get("duration"),
                "pitchbend": pb_value,
                "display_pitch": pitchbend_to_note_pitch(pb_value),
            }
        )
    return pad_notes


def apply_pad_edits(
    notes: List[Dict[str, Any]], pad_number: int, edited: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Apply edited notes back onto the original notes list."""
    updated: List[Dict[str, Any]] = [n for n in notes if n.get("noteNumber") != pad_number]
    for ed in edited:
        pb = note_pitch_to_pitchbend(ed.get("display_pitch", C2_NOTE))
        updated.append(
            {
                "noteNumber": pad_number,
                "startTime": ed.get("startTime"),
                "duration": ed.get("duration"),
                "velocity": ed.get("velocity", 127.0),
                "offVelocity": ed.get("offVelocity", 0.0),
                "automations": {"PitchBend": [{"time": 0.0, "value": pb}]},
            }
        )
    return updated
