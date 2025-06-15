from core.pitchbend_overlay import compute_overlay_notes, BASE_NOTE, SEMI_UNIT


def test_basic_semitones():
    notes = [{
        "noteNumber": 37,
        "startTime": 0.0,
        "duration": 1.0,
        "automations": {"PitchBend": [{"time": 0, "value": 0}]}
    }]
    overlay = compute_overlay_notes(notes, 37)
    assert overlay[0]["noteNumber"] == BASE_NOTE

    notes[0]["automations"]["PitchBend"][0]["value"] = SEMI_UNIT
    overlay = compute_overlay_notes(notes, 37)
    assert overlay[0]["noteNumber"] == BASE_NOTE + 1

    notes[0]["automations"]["PitchBend"][0]["value"] = -SEMI_UNIT
    overlay = compute_overlay_notes(notes, 37)
    assert overlay[0]["noteNumber"] == BASE_NOTE - 1


def test_overlay_generation():
    notes = [
        {
            "noteNumber": 40,
            "startTime": 0.0,
            "duration": 0.5,
            "automations": {"PitchBend": [{"time": 0, "value": SEMI_UNIT}]}
        },
        {
            "noteNumber": 41,
            "startTime": 0.5,
            "duration": 0.5,
            "automations": {"PitchBend": [{"time": 0, "value": SEMI_UNIT * 2}]}
        },
    ]
    overlay = compute_overlay_notes(notes, 41)
    assert len(overlay) == 1
    ov = overlay[0]
    assert ov["startTime"] == 0.5
    assert ov["duration"] == 0.5
    assert ov["noteNumber"] == BASE_NOTE + 2
