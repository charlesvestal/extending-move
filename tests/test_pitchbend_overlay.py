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
