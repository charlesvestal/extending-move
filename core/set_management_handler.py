import os
import json
import copy
from typing import Dict, List, Any, Optional

def create_set(set_name):
    """
    Create a blank set file in the UserLibrary/Sets directory.
    """
    directory = "/data/UserData/UserLibrary/Sets"
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, set_name)
    try:
        open(path, 'w').close()
        return {'success': True, 'message': f"Set '{set_name}' created successfully", 'path': path}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def load_set_template(template_path: str) -> Dict[str, Any]:
    """
    Load a set template from file.
    
    Args:
        template_path: Path to the template .abl file
        
    Returns:
        Dictionary containing the parsed set data
    """
    try:
        with open(template_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load template: {str(e)}")

def get_chord_definitions() -> Dict[str, List[int]]:
    """Get available chord definitions with intervals from root."""
    return {
        'C_major': [0, 4, 7],      # C, E, G
        'C_minor': [0, 3, 7],      # C, Eb, G
        'F_major': [0, 4, 7],      # F, A, C (will be transposed)
        'G_major': [0, 4, 7],      # G, B, D (will be transposed)
        'A_minor': [0, 3, 7],      # A, C, E (will be transposed)
        'D_minor': [0, 3, 7],      # D, F, A (will be transposed)
    }

def get_chord_root_notes() -> Dict[str, int]:
    """Get root note MIDI numbers for different chords."""
    return {
        'C_major': 60,   # C4
        'C_minor': 60,   # C4
        'F_major': 65,   # F4
        'G_major': 67,   # G4
        'A_minor': 57,   # A3
        'D_minor': 62,   # D4
    }

def generate_chord_set(set_name: str, chord_type: str = 'C_major', 
                      root_note: int = None, tempo: float = 152.0) -> Dict[str, Any]:
    """
    Generate a MIDI set with chord patterns on every downbeat.
    
    Args:
        set_name: Name for the new set
        chord_type: Type of chord to generate
        root_note: Root note MIDI number (overrides default for chord)
        tempo: Tempo in BPM
        
    Returns:
        Result dictionary with success status and message
    """
    try:
        # Load the template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
        song = load_set_template(template_path)
        
        # Get chord definition
        chord_definitions = get_chord_definitions()
        chord_roots = get_chord_root_notes()
        
        if chord_type not in chord_definitions:
            return {
                'success': False,
                'message': f"Unknown chord type: {chord_type}"
            }
        
        # Use provided root note or default for chord type
        if root_note is None:
            root_note = chord_roots[chord_type]
        
        # Get chord intervals
        chord_intervals = chord_definitions[chord_type]
        
        # Generate chord notes for every downbeat (beats 0, 1, 2, 3)
        new_notes = []
        for beat in [0.0, 1.0, 2.0, 3.0]:
            for interval in chord_intervals:
                new_notes.append({
                    'noteNumber': root_note + interval,
                    'startTime': beat,
                    'duration': 0.25,  # 1/16th note duration
                    'velocity': 100.0,
                    'offVelocity': 0.0
                })
        
        # Update the first track's first clip with chord notes
        song['tracks'][0]['clipSlots'][0]['clip']['notes'] = new_notes
        
        # Update set metadata
        song['rootNote'] = root_note % 12  # Root note class (0-11)
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
            'message': f"Chord set '{set_name}' with {chord_type} generated successfully",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to generate chord set: {str(e)}"
        }


# --- New function for generating chromatic scale set ---
def generate_chromatic_scale_set(set_name, root_note=5, tempo=152.0):
    """
    Generate a one-bar chromatic scale MIDI set programmatically.
    """
    # Load the template and offset notes to the desired root
    template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
    song = load_set_template(template_path)

    # Create a repeated single note at every other sixteenth step
    original_notes = song['tracks'][0]['clipSlots'][0]['clip']['notes']
    new_notes = []
    for i, note in enumerate(original_notes):
        if i % 2 == 0:
            new_notes.append({
                'noteNumber': root_note,
                'startTime': note['startTime'],
                'duration': note['duration'],
                'velocity': note['velocity'],
                'offVelocity': note['offVelocity']
            })
    song['tracks'][0]['clipSlots'][0]['clip']['notes'] = new_notes

    # Update set metadata
    song['rootNote'] = root_note
    song['tempo'] = tempo

    # Write out the modified set
    output_dir = "/data/UserData/UserLibrary/Sets"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, set_name)
    if not output_path.endswith('.abl'):
        output_path += '.abl'
    with open(output_path, 'w') as f:
        json.dump(song, f, indent=2)

    return {
        'success': True,
        'message': f"Chromatic scale set '{set_name}' generated",
        'path': output_path
    }
