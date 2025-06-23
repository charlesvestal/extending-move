# Audio Effect Parameter Schemas

The parameter lists for Ableton Live audio effects can be generated from the JSON presets found in `examples/Audio Effects/`. The helper script `utility-scripts/generate_effect_schemas.py` scans every preset, collects all parameters per device type and records the numeric ranges or enum options that occur.

Running the script creates schema files in `static/schemas/` for each effect kind, for example `autoFilter_schema.json` or `reverb_schema.json`. These schemas are primarily for documentation and tooling.

```bash
python3 utility-scripts/generate_effect_schemas.py
```

The script prints how many parameters were found for each effect.
