# Instrument Parameter Schemas

The project automatically extracts the available parameters for several Ableton Live instruments by scanning the preset JSON files under `core library files/`. For each instrument type the minimum and maximum numeric values observed are recorded along with possible enum options.

Generated schema files can be found in `static/schemas/`:

- `drift_schema.json`
- `wavetable_schema.json`
- `melodicSampler_schema.json`

These schemas are not currently used beyond documentation but provide a reference for building macro editors or validation tools.

Numeric entries may also include a `unit` and `decimals` key. The web editor uses
this metadata to format values—frequencies labeled `Hz` automatically switch to
`kHz` when above 1,000 and times labeled `s` display in milliseconds when below
one second. Gain parameters using a `dB` unit and ranges up to `2.0` (including
envelope sustain at `0.0–1.0`) are displayed as decibels to match Live's
controls.
