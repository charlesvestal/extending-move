# PitchBend Editing Mode for Drum Pads

## Summary
Extends the existing clip editor to allow editing per-pad PitchBend automation using the piano roll interface. Users can enter a special mode for any drum pad that reinterprets PitchBend values as pitched note blocks.

## Data Model
No new data structures are introduced. Each note already stores PitchBend automation data:

```json
{
  "noteNumber": 46,
  "startTime": 0.5,
  "duration": 0.25,
  "velocity": 127.0,
  "offVelocity": 0.0,
  "automations": {
    "PitchBend": [
      { "time": 0.0, "value": 341.2916564941406 }
    ]
  }
}
```

* Only the first PitchBend value at time `0.0` is used.
* Notes without a PitchBend entry are hidden when pitch editing.
* Pitch values are calculated relative to C2 with a scale of `170.6458282470703` units per semitone.

## User Flow
1. The clip editor displays a music-note icon on pad rows containing PitchBend data.
2. Clicking the icon enters PitchBend Editing Mode for that pad.

## PitchBend Editing Mode
* Only notes for the selected pad are shown.
* Notes are positioned vertically according to their PitchBend value relative to C2.
* Notes are rendered in blue instead of red.
* Notes behave as step notes with no curves or glides.
* The grid and editing interactions match normal clip mode.
* The pad is monophonic—notes cannot overlap.
* Editing a note updates its start time, duration and PitchBend value.

## Navigation
* Users can toggle in and out of pitch editing mode without saving.
* Changes persist in the original note data.
* The mode acts as a filtered view scoped to a single pad.

## Suggested Implementation
```javascript
const semitone = 170.6458282470703;
const baseNote = 48; // C2
const pitch = baseNote + pitchBendValue / semitone;
```
Introduce two flags in the clip editor state:

```javascript
pitchEditMode: boolean;
activePitchPad: number;
```
When `pitchEditMode` is true, filter notes to those matching `activePitchPad` and calculate their vertical position from the first PitchBend value.
