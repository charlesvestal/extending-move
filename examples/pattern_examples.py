#!/usr/bin/env python3
"""
Examples of using the MIDI pattern generator to create custom patterns.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

OUTPUT_DIR = os.environ.get("MOVE_SET_DIR", "/data/UserData/UserLibrary/Sets")

from core.midi_pattern_generator import (
    generate_pattern_set,
    create_c_major_downbeats,
    create_scale_pattern,
    create_rhythm_pattern
)

def example_1_c_major_chords():
    """Example 1: C major chords on every downbeat, 1/16th note long"""
    print("\n=== Example 1: C Major Chords on Downbeats ===")
    
    # Use the helper function
    pattern = create_c_major_downbeats(beats=4)
    
    # Generate the set
    result = generate_pattern_set(
        set_name="C_Major_Downbeats",
        pattern=pattern,
        clip_length=4.0,
        tempo=120.0,
        output_dir=OUTPUT_DIR
    )
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")

def example_2_custom_pattern():
    """Example 2: Custom pattern with different chords"""
    print("\n=== Example 2: Custom Chord Progression ===")
    
    # Create a I-V-vi-IV progression (C-G-Am-F)
    pattern = [
        # Beat 0: C major
        {'note': 'C4', 'start': 0.0, 'duration': 0.5},
        {'note': 'E4', 'start': 0.0, 'duration': 0.5},
        {'note': 'G4', 'start': 0.0, 'duration': 0.5},
        
        # Beat 1: G major
        {'note': 'G3', 'start': 1.0, 'duration': 0.5},
        {'note': 'B3', 'start': 1.0, 'duration': 0.5},
        {'note': 'D4', 'start': 1.0, 'duration': 0.5},
        
        # Beat 2: A minor
        {'note': 'A3', 'start': 2.0, 'duration': 0.5},
        {'note': 'C4', 'start': 2.0, 'duration': 0.5},
        {'note': 'E4', 'start': 2.0, 'duration': 0.5},
        
        # Beat 3: F major
        {'note': 'F3', 'start': 3.0, 'duration': 0.5},
        {'note': 'A3', 'start': 3.0, 'duration': 0.5},
        {'note': 'C4', 'start': 3.0, 'duration': 0.5},
    ]
    
    result = generate_pattern_set(
        set_name="Chord_Progression",
        pattern=pattern,
        clip_length=4.0,
        tempo=120.0,
        output_dir=OUTPUT_DIR
    )
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")

def example_3_scale_pattern():
    """Example 3: Scale patterns"""
    print("\n=== Example 3: Scale Patterns ===")
    
    # Create a C major scale
    pattern = create_scale_pattern(
        root='C4',
        scale_type='major',
        note_duration=0.25,  # 1/16th notes
        ascending=True
    )
    
    result = generate_pattern_set(
        set_name="C_Major_Scale",
        pattern=pattern,
        clip_length=4.0,
        tempo=120.0,
        output_dir=OUTPUT_DIR
    )
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")

def example_4_rhythm_pattern():
    """Example 4: Rhythmic pattern on a single note"""
    print("\n=== Example 4: Rhythmic Pattern ===")
    
    # Create a syncopated rhythm
    rhythm = [
        (0.0, 0.5),    # Beat 1: half note
        (0.75, 0.25),  # Syncopated 16th
        (1.5, 0.25),   # Beat 2.5: 16th
        (2.0, 0.25),   # Beat 3: 16th
        (2.5, 0.5),    # Beat 3.5: quarter
        (3.25, 0.25),  # Syncopated 16th
        (3.75, 0.25),  # Last 16th
    ]
    
    pattern = create_rhythm_pattern(
        note='C4',
        rhythm=rhythm,
        velocity_pattern=[100, 80, 90]  # Cycle through velocities
    )
    
    result = generate_pattern_set(
        set_name="Syncopated_Rhythm",
        pattern=pattern,
        clip_length=4.0,
        tempo=120.0,
        output_dir=OUTPUT_DIR
    )
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")

def example_5_complex_pattern():
    """Example 5: Complex pattern with melody and bass"""
    print("\n=== Example 5: Complex Pattern (Melody + Bass) ===")
    
    pattern = [
        # Bass line
        {'note': 'C2', 'start': 0.0, 'duration': 0.5, 'velocity': 90},
        {'note': 'C2', 'start': 0.5, 'duration': 0.5, 'velocity': 70},
        {'note': 'G2', 'start': 1.0, 'duration': 0.5, 'velocity': 90},
        {'note': 'G2', 'start': 1.5, 'duration': 0.5, 'velocity': 70},
        {'note': 'A2', 'start': 2.0, 'duration': 0.5, 'velocity': 90},
        {'note': 'A2', 'start': 2.5, 'duration': 0.5, 'velocity': 70},
        {'note': 'F2', 'start': 3.0, 'duration': 0.5, 'velocity': 90},
        {'note': 'F2', 'start': 3.5, 'duration': 0.5, 'velocity': 70},
        
        # Melody line
        {'note': 'E4', 'start': 0.0, 'duration': 0.75, 'velocity': 100},
        {'note': 'D4', 'start': 0.75, 'duration': 0.25, 'velocity': 80},
        {'note': 'C4', 'start': 1.0, 'duration': 0.5, 'velocity': 90},
        {'note': 'D4', 'start': 1.5, 'duration': 0.5, 'velocity': 85},
        {'note': 'E4', 'start': 2.0, 'duration': 0.25, 'velocity': 95},
        {'note': 'F4', 'start': 2.25, 'duration': 0.25, 'velocity': 90},
        {'note': 'G4', 'start': 2.5, 'duration': 0.5, 'velocity': 100},
        {'note': 'E4', 'start': 3.0, 'duration': 1.0, 'velocity': 95},
    ]
    
    result = generate_pattern_set(
        set_name="Melody_And_Bass",
        pattern=pattern,
        clip_length=4.0,
        tempo=120.0,
        output_dir=OUTPUT_DIR
    )
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")

def example_6_longer_clip():
    """Example 6: 8-bar pattern"""
    print("\n=== Example 6: 8-Bar Pattern ===")
    
    # Create an 8-bar pattern with variations
    pattern = []
    
    # First 4 bars: ascending arpeggio
    for bar in range(4):
        base_time = bar * 4.0
        for i, note in enumerate(['C4', 'E4', 'G4', 'C5']):
            pattern.append({
                'note': note,
                'start': base_time + i,
                'duration': 0.5,
                'velocity': 80 + i * 5
            })
    
    # Next 4 bars: descending arpeggio with different rhythm
    for bar in range(4, 8):
        base_time = bar * 4.0
        for i, note in enumerate(['C5', 'G4', 'E4', 'C4']):
            pattern.append({
                'note': note,
                'start': base_time + i * 0.75,  # Triplet feel
                'duration': 0.25,
                'velocity': 100 - i * 5
            })
    
    result = generate_pattern_set(
        set_name="Eight_Bar_Pattern",
        pattern=pattern,
        clip_length=32.0,  # 8 bars * 4 beats
        tempo=120.0,
        output_dir=OUTPUT_DIR
    )
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")

if __name__ == "__main__":
    print("MIDI Pattern Generator Examples")
    print("===============================")
    
    # Run all examples
    example_1_c_major_chords()
    example_2_custom_pattern()
    example_3_scale_pattern()
    example_4_rhythm_pattern()
    example_5_complex_pattern()
    example_6_longer_clip()
    
    print("\n✓ All examples completed!")
    print("\nNote: These examples assume the Move device is connected.")
    print("The output directory is configurable via the MOVE_SET_DIR environment variable.")
