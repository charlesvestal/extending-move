"""
MIDI pattern generator for creating custom note patterns in Ableton Live sets.
"""

import os
import json
from typing import Dict, List, Any, Tuple, Optional

from core.utils import load_set_template

def generate_pattern_set(
    set_name: str,
    pattern: List[Dict[str, Any]],
    clip_length: float = 4.0,
    tempo: float = 120.0
) -> Dict[str, Any]:
    """
    Generate an Ableton Live set with a custom pattern of notes.
    
    Args:
        set_name: Name for the new set
        pattern: List of note dictionaries, each containing:
            - 'note': MIDI note number (0-127) or note name (e.g., 'C4', 'D#5')
            - 'start': Start time in beats (e.g., 0, 0.5, 1.0)
            - 'duration': Duration in beats (e.g., 0.25 for 1/16th note)
            - 'velocity': Optional velocity (1-127, default 100)
        clip_length: Length of the clip in beats (default 4.0)
        tempo: Tempo in BPM (default 120)
        
    Returns:
        Result dictionary with success status and message
        
    Example:
        # C major chord on every downbeat, 1/16th note long
        pattern = [
            {'note': 'C4', 'start': 0.0, 'duration': 0.25},
            {'note': 'E4', 'start': 0.0, 'duration': 0.25},
            {'note': 'G4', 'start': 0.0, 'duration': 0.25},
            {'note': 'C4', 'start': 1.0, 'duration': 0.25},
            {'note': 'E4', 'start': 1.0, 'duration': 0.25},
            {'note': 'G4', 'start': 1.0, 'duration': 0.25},
            # ... etc
        ]
    """
    try:
        # Load the template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
        song = load_set_template(template_path)
        
        # Convert pattern to Ableton format
        notes = []
        for note_info in pattern:
            # Parse note (handle both MIDI numbers and note names)
            note_value = note_info['note']
            if isinstance(note_value, str):
                note_number = note_name_to_midi(note_value)
            else:
                note_number = int(note_value)
            
            # Validate note number
            if not 0 <= note_number <= 127:
                raise ValueError(f"Invalid MIDI note number: {note_number}")
            
            # Create note entry
            notes.append({
                'noteNumber': note_number,
                'startTime': float(note_info['start']),
                'duration': float(note_info['duration']),
                'velocity': float(note_info.get('velocity', 100)),
                'offVelocity': 0.0
            })
        
        # Update the clip
        clip = song['tracks'][0]['clipSlots'][0]['clip']
        clip['notes'] = notes
        clip['region']['end'] = clip_length
        clip['region']['loop']['end'] = clip_length
        
        # Update set metadata
        song['tempo'] = tempo
        
        # Save the modified set
        output_dir = "/data/UserData/UserLibrary/Sets"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, set_name)
        if not output_path.endswith('.abl'):
            output_path += '.abl'
        
        with open(output_path, 'w') as f:
            json.dump(song, f, indent=2)
        
        return {
            'success': True,
            'message': f"Pattern set '{set_name}' generated successfully ({len(notes)} notes)",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to generate pattern set: {str(e)}"
        }

def note_name_to_midi(note_name: str) -> int:
    """
    Convert note name to MIDI number.
    Examples: 'C4' -> 60, 'D#5' -> 75, 'Bb3' -> 58
    """
    # Note name mapping (C = 0, D = 2, etc.)
    note_map = {
        'C': 0, 'D': 2, 'E': 4, 'F': 5, 
        'G': 7, 'A': 9, 'B': 11
    }
    
    # Parse note name
    note_name = note_name.strip().upper()
    
    # Extract base note
    base_note = note_name[0]
    if base_note not in note_map:
        raise ValueError(f"Invalid note name: {note_name}")
    
    # Check for accidentals
    offset = 0
    idx = 1
    if idx < len(note_name):
        if note_name[idx] == '#':
            offset = 1
            idx += 1
        elif note_name[idx] == 'B':  # Flat
            offset = -1
            idx += 1
    
    # Extract octave
    octave_str = note_name[idx:]
    try:
        octave = int(octave_str)
    except ValueError:
        raise ValueError(f"Invalid octave in note name: {note_name}")
    
    # Calculate MIDI number (C4 = 60)
    midi_number = (octave + 1) * 12 + note_map[base_note] + offset
    
    return midi_number

def create_c_major_downbeats(beats: int = 4) -> List[Dict[str, Any]]:
    """
    Helper function to create C major chords on every downbeat.
    
    Args:
        beats: Number of beats in the measure (default 4)
        
    Returns:
        Pattern list for use with generate_pattern_set
    """
    pattern = []
    for beat in range(beats):
        # Add C major triad (C, E, G)
        pattern.extend([
            {'note': 'C4', 'start': float(beat), 'duration': 0.25},
            {'note': 'E4', 'start': float(beat), 'duration': 0.25},
            {'note': 'G4', 'start': float(beat), 'duration': 0.25},
        ])
    return pattern

def create_scale_pattern(
    root: str = 'C4',
    scale_type: str = 'major',
    note_duration: float = 0.25,
    ascending: bool = True
) -> List[Dict[str, Any]]:
    """
    Helper function to create scale patterns.
    
    Args:
        root: Root note (e.g., 'C4')
        scale_type: 'major', 'minor', 'pentatonic', etc.
        note_duration: Duration of each note in beats
        ascending: Whether to go up or down the scale
        
    Returns:
        Pattern list for use with generate_pattern_set
    """
    # Scale intervals from root
    scales = {
        'major': [0, 2, 4, 5, 7, 9, 11, 12],
        'minor': [0, 2, 3, 5, 7, 8, 10, 12],
        'pentatonic': [0, 2, 4, 7, 9, 12],
        'blues': [0, 3, 5, 6, 7, 10, 12],
        'chromatic': list(range(13))
    }
    
    if scale_type not in scales:
        raise ValueError(f"Unknown scale type: {scale_type}")
    
    intervals = scales[scale_type]
    if not ascending:
        intervals = intervals[::-1]
    
    root_midi = note_name_to_midi(root)
    pattern = []
    
    for i, interval in enumerate(intervals):
        pattern.append({
            'note': root_midi + interval,
            'start': i * note_duration,
            'duration': note_duration,
            'velocity': 100
        })
    
    return pattern

def create_rhythm_pattern(
    note: str,
    rhythm: List[Tuple[float, float]],
    velocity_pattern: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Helper function to create rhythmic patterns on a single note.
    
    Args:
        note: Note to play (e.g., 'C4')
        rhythm: List of (start_time, duration) tuples in beats
        velocity_pattern: Optional list of velocities to cycle through
        
    Returns:
        Pattern list for use with generate_pattern_set
        
    Example:
        # Syncopated rhythm
        rhythm = [(0, 0.5), (0.75, 0.25), (1.5, 0.5), (2.25, 0.25), (3, 0.5)]
    """
    pattern = []
    velocities = velocity_pattern or [100]
    
    for i, (start, duration) in enumerate(rhythm):
        velocity = velocities[i % len(velocities)]
        pattern.append({
            'note': note,
            'start': start,
            'duration': duration,
            'velocity': velocity
        })
    
    return pattern
