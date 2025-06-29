# Instrument Parameter Schemas

The project automatically extracts the available parameters for several Ableton Live instruments by scanning the preset JSON files under `core library files/`. For each instrument type the minimum and maximum numeric values observed are recorded along with possible enum options.

Generated schema files can be recreated using `utility-scripts/generate_instrument_schemas.py`.
The resulting files are stored in `static/schemas/`:

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

The Melodic Sampler schema now includes unit and decimal information so parameter values match Ableton Live. Playback controls use percentages, transpose is in semitones, detune is in cents, envelope times use seconds, and filter settings include proper frequency, resonance, and gain ranges.
