import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.midi_pattern_generator import (
    note_name_to_midi,
    midi_to_note_name,
    create_scale_pattern,
    create_rhythm_pattern,
)


def test_note_name_to_midi_basic():
    assert note_name_to_midi("C4") == 60
    assert note_name_to_midi("D#5") == 75
    assert note_name_to_midi("Bb3") == 58


def test_note_name_to_midi_invalid():
    import pytest
    with pytest.raises(ValueError):
        note_name_to_midi("H2")
    with pytest.raises(ValueError):
        note_name_to_midi("C?")


def test_midi_to_note_name_basic():
    assert midi_to_note_name(60) == "C4"
    assert midi_to_note_name(75) == "D#5"
    assert midi_to_note_name(58) == "A#3"


def test_midi_to_note_name_invalid():
    import pytest
    with pytest.raises(ValueError):
        midi_to_note_name(-1)
    with pytest.raises(ValueError):
        midi_to_note_name(128)


def test_create_scale_pattern_descending():
    pattern = create_scale_pattern("C4", "major", note_duration=0.5, ascending=False)
    assert pattern[0]["note"] > pattern[-1]["note"]
    assert len(pattern) == 8
    assert pattern[1]["start"] == 0.5


def test_create_rhythm_pattern_velocity_cycle():
    rhythm = [(0, 0.25), (0.5, 0.25), (1.0, 0.25), (1.5, 0.25)]
    pattern = create_rhythm_pattern("C4", rhythm, velocity_pattern=[80, 100])
    velocities = [n["velocity"] for n in pattern]
    assert velocities == [80, 100, 80, 100]
    assert [n["start"] for n in pattern] == [0, 0.5, 1.0, 1.5]
