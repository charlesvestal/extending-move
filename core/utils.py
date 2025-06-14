import json
from typing import Any, Dict


def load_set_template(template_path: str) -> Dict[str, Any]:
    """Load a set template from ``template_path`` and return the parsed data."""
    try:
        with open(template_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load template: {str(e)}")


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_note_name(midi_number: int) -> str:
    """Convert a MIDI note number to a note name like ``C4``."""
    if not 0 <= midi_number <= 127:
        raise ValueError(f"Invalid MIDI note number: {midi_number}")
    octave = midi_number // 12 - 1
    name = NOTE_NAMES[midi_number % 12]
    return f"{name}{octave}"

