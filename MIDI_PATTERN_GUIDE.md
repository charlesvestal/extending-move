# MIDI Pattern Generator Guide

This guide explains how to use the MIDI pattern generator to create custom note patterns for Ableton Live sets.

## Overview

The MIDI pattern generator allows you to:
- Create arbitrary patterns of notes and rhythms
- Adjust the length of clips
- Generate sets from MIDI files
- Use helper functions for common patterns

## Basic Usage

### 1. Simple C Major Chord Example

The simplest example creates C major chords on every downbeat:

```python
from core.set_management_handler import generate_c_major_chord_example

result = generate_c_major_chord_example("My_C_Major_Set", tempo=120.0)
```

This creates a 4-beat measure with C major triads (C, E, G) on beats 1, 2, 3, and 4, each lasting 1/16th note.

### 2. Custom Pattern Generation

For more control, use the pattern generator directly:

```python
from core.midi_pattern_generator import generate_pattern_set

# Define your pattern
pattern = [
    {'note': 'C4', 'start': 0.0, 'duration': 0.25},  # C on beat 1
    {'note': 'E4', 'start': 0.0, 'duration': 0.25},  # E on beat 1
    {'note': 'G4', 'start': 0.0, 'duration': 0.25},  # G on beat 1
    {'note': 'C4', 'start': 1.0, 'duration': 0.25},  # C on beat 2
    # ... continue pattern
]

result = generate_pattern_set(
    set_name="My_Pattern",
    pattern=pattern,
    clip_length=4.0,  # 4 beats
    tempo=120.0
)
```

### 3. Pattern Dictionary Format

Each note in the pattern is a dictionary with:
- `note`: MIDI number (0-127) or note name ('C4', 'D#5', etc.)
- `start`: Start time in beats (0.0 = beat 1, 1.0 = beat 2, etc.)
- `duration`: Duration in beats (0.25 = 1/16th note, 0.5 = 1/8th note, etc.)
- `velocity`: Optional velocity (1-127, default 100)

### 4. Helper Functions

#### Create C Major Chords on Downbeats
```python
from core.midi_pattern_generator import create_c_major_downbeats

pattern = create_c_major_downbeats(beats=4)  # 4-beat measure
```

#### Create Scale Patterns
```python
from core.midi_pattern_generator import create_scale_pattern

pattern = create_scale_pattern(
    root='C4',
    scale_type='major',  # Options: 'major', 'minor', 'pentatonic', 'blues', 'chromatic'
    note_duration=0.25,  # 1/16th notes
    ascending=True
)
```

#### Create Rhythm Patterns
```python
from core.midi_pattern_generator import create_rhythm_pattern

# Define rhythm as (start_time, duration) tuples
rhythm = [
    (0.0, 0.5),    # Beat 1: half note
    (0.75, 0.25),  # Syncopated 16th
    (1.5, 0.25),   # Beat 2.5: 16th
    (2.0, 0.25),   # Beat 3: 16th
]

pattern = create_rhythm_pattern(
    note='C4',
    rhythm=rhythm,
    velocity_pattern=[100, 80, 90]  # Cycle through velocities
)
```

## MIDI File Upload

You can also generate sets from MIDI files through the web interface:

1. Navigate to the Set Management page
2. Upload a .mid or .midi file
3. Specify a set name and optional tempo
4. Select a pad and color for the device
5. Click "Generate Set from MIDI"

## Examples

See `examples/pattern_examples.py` for comprehensive examples including:
- C major chords on downbeats
- Custom chord progressions
- Scale patterns
- Rhythmic patterns
- Complex patterns with melody and bass
- Multi-bar patterns

Run the examples:
```bash
python examples/pattern_examples.py
```

## Note Timing Reference

- 1 beat = 1.0
- 1/2 note = 0.5
- 1/4 note = 0.25
- 1/8 note = 0.125
- 1/16 note = 0.0625
- 1/32 note = 0.03125

## Note Name Reference

Note names follow the format: `[Note][Accidental][Octave]`
- Notes: C, D, E, F, G, A, B
- Accidentals: # (sharp), b (flat)
- Octave: Number (C4 = middle C = MIDI 60)

Examples:
- `C4` = Middle C (MIDI 60)
- `D#5` = D sharp above middle C (MIDI 75)
- `Bb3` = B flat below middle C (MIDI 58)
