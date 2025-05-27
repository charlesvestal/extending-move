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

def generate_note_pattern(pattern_type: str, base_note: int = 48, 
                         velocity: int = 127, duration: float = 0.25,
                         num_steps: int = 16) -> List[Dict[str, Any]]:
    """
    Generate different note patterns for a 16-step sequence.
    
    Args:
        pattern_type: Type of pattern ('kick', 'snare', 'hihat', 'custom')
        base_note: MIDI note number
        velocity: Note velocity (0-127)
        duration: Note duration in quarter notes
        num_steps: Number of steps in the pattern
        
    Returns:
        List of note dictionaries
    """
    notes = []
    
    if pattern_type == 'kick':
        # Four-on-the-floor pattern
        for i in range(4):
            notes.append({
                "noteNumber": base_note,
                "startTime": i * 1.0,
                "duration": duration,
                "velocity": float(velocity),
                "offVelocity": 0.0
            })
    
    elif pattern_type == 'snare':
        # Snare on 2 and 4
        notes.extend([
            {
                "noteNumber": base_note,
                "startTime": 1.0,
                "duration": duration,
                "velocity": float(velocity),
                "offVelocity": 0.0
            },
            {
                "noteNumber": base_note,
                "startTime": 3.0,
                "duration": duration,
                "velocity": float(velocity),
                "offVelocity": 0.0
            }
        ])
    
    elif pattern_type == 'hihat':
        # 16th note hi-hat pattern
        for i in range(16):
            notes.append({
                "noteNumber": base_note,
                "startTime": i * 0.25,
                "duration": duration,
                "velocity": float(velocity),
                "offVelocity": 0.0
            })
    
    elif pattern_type == 'offbeat':
        # Offbeat pattern
        for i in range(8):
            notes.append({
                "noteNumber": base_note,
                "startTime": i * 0.5 + 0.25,
                "duration": duration,
                "velocity": float(velocity),
                "offVelocity": 0.0
            })
    
    elif pattern_type == 'syncopated':
        # Syncopated pattern
        positions = [0.0, 0.75, 1.25, 2.0, 2.5, 3.0, 3.75]
        for pos in positions:
            notes.append({
                "noteNumber": base_note,
                "startTime": pos,
                "duration": duration,
                "velocity": float(velocity),
                "offVelocity": 0.0
            })
    
    elif pattern_type == 'custom':
        # Custom pattern - can be extended with more parameters
        pass
    
    return notes

def modify_note_lanes(notes: List[Dict[str, Any]], 
                     pitch_shift: int = 0,
                     velocity_scale: float = 1.0,
                     time_scale: float = 1.0,
                     swing: float = 0.0) -> List[Dict[str, Any]]:
    """
    Modify existing note lanes with various transformations.
    
    Args:
        notes: List of note dictionaries
        pitch_shift: Number of semitones to shift (positive or negative)
        velocity_scale: Scale factor for velocity (0.0 to 2.0)
        time_scale: Scale factor for timing (0.5 = double speed, 2.0 = half speed)
        swing: Swing amount (0.0 to 1.0, where 0.5 = 50% swing)
        
    Returns:
        Modified list of note dictionaries
    """
    modified_notes = []
    
    for i, note in enumerate(notes):
        new_note = copy.deepcopy(note)
        
        # Apply pitch shift
        new_note['noteNumber'] = max(0, min(127, note['noteNumber'] + pitch_shift))
        
        # Apply velocity scaling
        new_velocity = note['velocity'] * velocity_scale
        new_note['velocity'] = max(0.0, min(127.0, new_velocity))
        
        # Apply time scaling
        new_note['startTime'] = note['startTime'] * time_scale
        new_note['duration'] = note['duration'] * time_scale
        
        # Apply swing (affects every other 16th note)
        if swing > 0 and i % 2 == 1:
            swing_amount = swing * 0.25  # Max swing is 25% of a 16th note
            new_note['startTime'] += swing_amount
        
        modified_notes.append(new_note)
    
    return modified_notes

def generate_set_from_template(set_name: str, 
                             template_path: str = None,
                             tracks_config: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a new set based on a template with modified note lanes.
    
    Args:
        set_name: Name for the new set
        template_path: Path to template .abl file (defaults to Song.abl)
        tracks_config: List of track configurations with note patterns
        
    Returns:
        Result dictionary with success status and message
    """
    try:
        # Use default template if not specified
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), 
                                       '..', 'examples', 'Sets', 'Song.abl')
        
        # Load template
        set_data = load_set_template(template_path)
        
        # Apply track configurations if provided
        if tracks_config:
            for i, track_config in enumerate(tracks_config):
                if i >= len(set_data['tracks']):
                    break
                
                track = set_data['tracks'][i]
                
                # Find the first clip slot with a clip
                for clip_slot in track.get('clipSlots', []):
                    if clip_slot.get('clip'):
                        # Generate or modify notes based on configuration
                        pattern_type = track_config.get('pattern', 'kick')
                        base_note = track_config.get('note', 48)
                        velocity = track_config.get('velocity', 127)
                        
                        # Generate base pattern
                        new_notes = generate_note_pattern(
                            pattern_type, base_note, velocity
                        )
                        
                        # Apply modifications if specified
                        if 'modifications' in track_config:
                            mods = track_config['modifications']
                            new_notes = modify_note_lanes(
                                new_notes,
                                pitch_shift=mods.get('pitch_shift', 0),
                                velocity_scale=mods.get('velocity_scale', 1.0),
                                time_scale=mods.get('time_scale', 1.0),
                                swing=mods.get('swing', 0.0)
                            )
                        
                        # Update clip notes
                        clip_slot['clip']['notes'] = new_notes
                        break
        
        # Save the modified set
        output_dir = "/data/UserData/UserLibrary/Sets"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, set_name)
        if not output_path.endswith('.abl'):
            output_path += '.abl'
        
        with open(output_path, 'w') as f:
            json.dump(set_data, f, indent=2)
        
        return {
            'success': True,
            'message': f"Set '{set_name}' generated successfully",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to generate set: {str(e)}"
        }

def get_available_patterns() -> List[str]:
    """Get list of available note patterns."""
    return ['kick', 'snare', 'hihat', 'offbeat', 'syncopated']

def get_drum_note_mappings() -> Dict[str, int]:
    """Get common drum note mappings."""
    return {
        'kick': 36,
        'snare': 38,
        'closed_hihat': 42,
        'open_hihat': 46,
        'crash': 49,
        'ride': 51,
        'tom_low': 43,
        'tom_mid': 47,
        'tom_high': 48
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
