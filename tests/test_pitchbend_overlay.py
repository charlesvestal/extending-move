import json
import subprocess
from pathlib import Path

JS_PATH = Path(__file__).resolve().parents[1] / 'static' / 'pitchbend_overlay.js'


def run_node(notes, row, ticks=96, expr=None):
    script = f"""
import {{computeOverlayNotes, BASE_NOTE, SEMI_UNIT, noteNumberToPitchbend}} from 'file://{JS_PATH.as_posix()}';
const notes = {json.dumps(notes)};
const result = computeOverlayNotes(notes, {row}, {ticks});
const val = {expr if expr is not None else 'BASE_NOTE'};
const pitch = noteNumberToPitchbend(val);
console.log(JSON.stringify({{'overlay': result, 'BASE_NOTE': BASE_NOTE, 'SEMI_UNIT': SEMI_UNIT, 'pitch': pitch}}));
"""
    proc = subprocess.run(['node', '--input-type=module', '-e', script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def run_edit(note, new_note_number):
    """Return note after applying pitchbend edit using JS constants."""
    script = f"""
import {{noteNumberToPitchbend}} from 'file://{JS_PATH.as_posix()}';
let note = {json.dumps(note)};
if (!note.a) note.a = {{}};
note.a.PitchBend = [{{time: 0, value: noteNumberToPitchbend({new_note_number})}}];
console.log(JSON.stringify(note));
"""
    proc = subprocess.run(['node', '--input-type=module', '-e', script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def test_basic_semitones():
    notes = [{
        'n': 37,
        't': 0,
        'g': 96,
        'a': {'PitchBend': [{'time': 0, 'value': 0}]}
    }]
    result = run_node(notes, 37)
    assert result['overlay'][0]['noteNumber'] == result['BASE_NOTE']

    notes[0]['a']['PitchBend'][0]['value'] = result['SEMI_UNIT']
    result = run_node(notes, 37)
    assert result['overlay'][0]['noteNumber'] == result['BASE_NOTE'] + 1

    notes[0]['a']['PitchBend'][0]['value'] = -result['SEMI_UNIT']
    result = run_node(notes, 37)
    assert result['overlay'][0]['noteNumber'] == result['BASE_NOTE'] - 1


def test_overlay_generation():
    notes = [
        {
            'n': 40,
            't': 0,
            'g': 48,
            'a': {'PitchBend': [{'time': 0, 'value': 170.6458282470703}]}
        },
        {
            'n': 41,
            't': 48,
            'g': 48,
            'a': {'PitchBend': [{'time': 0, 'value': 341.2916564941406}]}
        }
    ]
    result = run_node(notes, 41)
    overlay = result['overlay']
    assert len(overlay) == 1
    ov = overlay[0]
    assert ov['startTime'] == 0.5
    assert ov['duration'] == 0.5
    assert ov['noteNumber'] == result['BASE_NOTE'] + 2
    assert ov['index'] == 1


def test_pitch_conversion():
    result = run_node([], 0, expr='BASE_NOTE + 2')
    assert abs(result['pitch'] - 2 * result['SEMI_UNIT']) < 1e-6


def test_edit_replaces_automation_and_preserves_others():
    note = {
        'n': 60,
        't': 0,
        'g': 96,
        'a': {
            'PitchBend': [
                {'time': 0, 'value': 123},
                {'time': 0.5, 'value': 456},
            ],
            'Pressure': [
                {'time': 0.25, 'value': 0.8}
            ]
        }
    }
    edited = run_edit(note, 62)
    assert 'Pressure' in edited['a']
    assert edited['a']['Pressure'] == note['a']['Pressure']
    pb = edited['a'].get('PitchBend')
    assert isinstance(pb, list) and len(pb) == 1
    assert pb[0]['time'] == 0
    result = run_node([], 0, expr='BASE_NOTE + 26')
    assert abs(pb[0]['value'] - result['pitch']) < 1e-6
