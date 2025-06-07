from pathlib import Path
from core.synth_preset_inspector_handler import (
    load_drift_schema,
    extract_parameter_values,
)
from core.synth_param_editor_handler import update_parameter_values

SCHEMA = load_drift_schema()
BASE_PRESET = Path('examples/Track Presets/Drift/Analog Shape.ablpreset')


def validate_value(name, value):
    meta = SCHEMA.get(name)
    if not meta:
        return True
    typ = meta.get('type')
    if typ == 'number':
        if not isinstance(value, (int, float)):
            return False
        if meta.get('min') is not None and value < meta['min']:
            return False
        if meta.get('max') is not None and value > meta['max']:
            return False
        if meta.get('decimals') == 0 and not float(value).is_integer():
            return False
    elif typ == 'boolean':
        if isinstance(value, bool):
            return True
        if value not in (0, 1):
            return False
    elif typ == 'enum':
        if value not in meta.get('options', []):
            return False
    return True


def load_values(preset):
    info = extract_parameter_values(str(preset))
    assert info['success'], info['message']
    return {p['name']: p['value'] for p in info['parameters']}


def test_base_preset_key_params_valid(tmp_path):
    values = load_values(BASE_PRESET)
    assert validate_value('Global_Transpose', values['Global_Transpose'])
    assert validate_value('Filter_NoiseThrough', values['Filter_NoiseThrough'])


def test_invalid_transpose(tmp_path):
    dest = tmp_path / 'invalid.ablpreset'
    update_parameter_values(str(BASE_PRESET), {'Global_Transpose': '0.5'}, str(dest))
    vals = load_values(dest)
    assert not validate_value('Global_Transpose', vals['Global_Transpose'])


def test_invalid_filter_through(tmp_path):
    dest = tmp_path / 'invalid.ablpreset'
    update_parameter_values(str(BASE_PRESET), {'Filter_NoiseThrough': '2'}, str(dest))
    vals = load_values(dest)
    assert not validate_value('Filter_NoiseThrough', vals['Filter_NoiseThrough'])
