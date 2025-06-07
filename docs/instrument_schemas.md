# Instrument Parameter Schemas

The project automatically extracts the available parameters for several Ableton Live instruments by scanning the preset JSON files under `core library files/`. For each instrument type the minimum and maximum numeric values observed are recorded along with possible enum options.

Generated schema files can be found in `static/schemas/`:

- `drift_schema.json`
- `wavetable_schema.json`
- `melodicSampler_schema.json`

These schemas are not currently used beyond documentation but provide a reference for building macro editors or validation tools.
