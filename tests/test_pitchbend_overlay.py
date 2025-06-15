import json
import subprocess
from pathlib import Path

JS_PATH = Path(__file__).resolve().parents[1] / 'static' / 'pitchbend_overlay.js'


def run_node(notes, row, ticks=96):
    script = f"""
import {{computeOverlayNotes, BASE_NOTE, SEMI_UNIT}} from 'file://{JS_PATH.as_posix()}';
const notes = {json.dumps(notes)};
const result = computeOverlayNotes(notes, {row}, {ticks});
console.log(JSON.stringify({{'overlay': result, 'BASE_NOTE': BASE_NOTE, 'SEMI_UNIT': SEMI_UNIT}}));
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
    assert result['overlay'][0]['eventIndex'] == 0

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
    assert ov['eventIndex'] == 1


def test_overlay_default_value():
    notes = [
        {'n': 50, 't': 0, 'g': 96},
        {'n': 50, 't': 96, 'g': 96, 'a': {'PitchBend': [{'time': 0, 'value': 0}]}}
    ]
    result = run_node(notes, 50)
    assert len(result['overlay']) == 2
    assert result['overlay'][0]['noteNumber'] == result['BASE_NOTE']
    assert result['overlay'][0]['eventIndex'] == 0
