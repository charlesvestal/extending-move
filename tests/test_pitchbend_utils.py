import json
from core.set_inspector_handler import extract_pitch_edit_notes, apply_pitch_edit_changes


def test_extract_and_apply_pitch_edit_notes():
    notes = [
        {
            "noteNumber": 46,
            "startTime": 0.5,
            "duration": 0.25,
            "velocity": 127.0,
            "offVelocity": 0.0,
            "automations": {
                "PitchBend": [
                    {"time": 0.0, "value": 341.2916564941406}
                ]
            }
        },
        {  # another pad
            "noteNumber": 47,
            "startTime": 1.0,
            "duration": 0.5,
            "velocity": 100.0,
            "offVelocity": 0.0,
            "automations": {}
        }
    ]

    pitch_notes = extract_pitch_edit_notes(notes, 46)
    assert len(pitch_notes) == 1
    # 341.2917 / 170.6458 = 2 semitones above C2 -> D2 (50)
    assert pitch_notes[0]["noteNumber"] == 50
    assert pitch_notes[0]["startTime"] == 0.5

    # modify pitch and apply back
    edit = [{"noteNumber": 51, "startTime": 0.75, "duration": 0.25, "velocity": 120.0, "offVelocity": 0.0}]
    updated = apply_pitch_edit_changes(notes, 46, edit)
    updated_note = updated[0]
    assert abs(updated_note["automations"]["PitchBend"][0]["value"] - ((51 - 48) * 170.6458282470703)) < 1e-6
    assert updated_note["startTime"] == 0.75
    assert updated_note["duration"] == 0.25
