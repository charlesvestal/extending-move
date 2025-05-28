import os
import json
import copy
import mido
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

def generate_c_major_chord_example(set_name: str, tempo: float = 120.0) -> Dict[str, Any]:
    """
    Example function that generates C major chords on every downbeat.
    Each chord is 1/16th note long in a 4 beat measure.
    
    Args:
        set_name: Name for the new set
        tempo: Tempo in BPM (default 120)
        
    Returns:
        Result dictionary with success status and message
    """
    try:
        # Load the template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
        song = load_set_template(template_path)
        
        # C major chord intervals: C (0), E (4), G (7)
        c_major_intervals = [0, 4, 7]
        root_note = 60  # Middle C (C4)
        
        # Generate chord notes for every downbeat (beats 0, 1, 2, 3)
        new_notes = []
        for beat in [0.0, 1.0, 2.0, 3.0]:
            for interval in c_major_intervals:
                new_notes.append({
                    'noteNumber': root_note + interval,
                    'startTime': beat,
                    'duration': 0.25,  # 1/16th note duration
                    'velocity': 100.0,
                    'offVelocity': 0.0
                })
        
        # Update the first track's first clip with chord notes
        clip = song['tracks'][0]['clipSlots'][0]['clip']
        clip['notes'] = new_notes
        
        # Ensure clip is 4 beats long
        clip['region']['end'] = 4.0
        clip['region']['loop']['end'] = 4.0
        
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
            'message': f"C major chord set '{set_name}' generated successfully",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to generate chord set: {str(e)}"
        }


def generate_midi_set_from_file(set_name: str, midi_file_path: str, tempo: float = None) -> Dict[str, Any]:
    """
    Generate an Ableton Live set from an uploaded MIDI file.
    
    Args:
        set_name: Name for the new set
        midi_file_path: Path to the uploaded MIDI file
        tempo: Tempo in BPM (if None, will try to detect from MIDI or use 120)
        
    Returns:
        Result dictionary with success status and message
    """
    try:
        # Load the MIDI file
        mid = mido.MidiFile(midi_file_path)
        
        # Try to detect tempo from MIDI file
        detected_tempo = 120.0  # Default tempo
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    # Convert microseconds per beat to BPM
                    detected_tempo = 60000000 / msg.tempo
                    break
            if detected_tempo != 120.0:
                break
        
        # Use provided tempo or detected tempo
        if tempo is None:
            tempo = detected_tempo
        
        # Extract notes from MIDI
        notes = []
        current_time = 0
        active_notes = {}  # Track active notes by note number
        
        # Find the first track with note data
        note_track = None
        for track in mid.tracks:
            has_notes = any(msg.type in ['note_on', 'note_off'] for msg in track)
            if has_notes:
                note_track = track
                break
        
        if note_track is None:
            return {
                'success': False,
                'message': "No note data found in MIDI file"
            }
        
        # Process the track to extract notes
        ticks_per_beat = mid.ticks_per_beat
        
        for msg in note_track:
            current_time += msg.time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                # Note on event
                active_notes[msg.note] = {
                    'start_time': current_time / ticks_per_beat,
                    'velocity': msg.velocity
                }
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Note off event
                if msg.note in active_notes:
                    start_beat = active_notes[msg.note]['start_time']
                    duration = (current_time / ticks_per_beat) - start_beat
                    
                    # Only add notes with positive duration
                    if duration > 0:
                        notes.append({
                            'noteNumber': msg.note,
                            'startTime': start_beat,
                            'duration': duration,
                            'velocity': float(active_notes[msg.note]['velocity']),
                            'offVelocity': 0.0
                        })
                    
                    del active_notes[msg.note]
        
        # Handle any remaining active notes (in case file ends without note_off)
        final_time = current_time / ticks_per_beat
        for note_num, note_data in active_notes.items():
            duration = final_time - note_data['start_time']
            if duration > 0:
                notes.append({
                    'noteNumber': note_num,
                    'startTime': note_data['start_time'],
                    'duration': duration,
                    'velocity': float(note_data['velocity']),
                    'offVelocity': 0.0
                })
        
        if not notes:
            return {
                'success': False,
                'message': "No valid notes found in MIDI file"
            }
        
        # Sort notes by start time
        notes.sort(key=lambda x: x['startTime'])
        
        # Calculate clip length (round up to nearest bar)
        max_end_time = max(note['startTime'] + note['duration'] for note in notes)
        clip_length = max(4.0, ((int(max_end_time) // 4) + 1) * 4.0)
        
        # Load the template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
        song = load_set_template(template_path)
        
        # Update the clip with MIDI notes
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
            'message': f"MIDI set '{set_name}' generated successfully ({len(notes)} notes imported)",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to process MIDI file: {str(e)}"
        }


# --- Drum set generation from MIDI file ---
def generate_drum_set_from_file(set_name: str, midi_file_path: str, tempo: float = None) -> Dict[str, Any]:
    """
    Generate an Ableton Live set from an uploaded drum MIDI file,
    mapping incoming notes to 16 pads starting at MIDI note 36.
    """
    try:
        # Load the MIDI file
        mid = mido.MidiFile(midi_file_path)

        # Tempo detection (reuse melodic logic)
        detected_tempo = 120.0
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    detected_tempo = 60000000 / msg.tempo
                    break
            if detected_tempo != 120.0:
                break

        if tempo is None:
            tempo = detected_tempo

        # Extract notes from first track with note events
        notes = []
        current_time = 0
        active_notes: Dict[int, Dict[str, Any]] = {}
        note_track = next((t for t in mid.tracks if any(m.type in ['note_on', 'note_off'] for m in t)), None)
        if note_track is None:
            return {'success': False, 'message': "No note data found in MIDI file"}
        ticks_per_beat = mid.ticks_per_beat

        for msg in note_track:
            current_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = {'start_time': current_time / ticks_per_beat, 'velocity': msg.velocity}
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    start = active_notes[msg.note]['start_time']
                    duration = (current_time / ticks_per_beat) - start
                    if duration > 0:
                        notes.append({
                            'noteNumber': msg.note,
                            'startTime': start,
                            'duration': duration,
                            'velocity': float(active_notes[msg.note]['velocity']),
                            'offVelocity': 0.0
                        })
                    del active_notes[msg.note]

        # Close out any lingering notes
        final_time = current_time / ticks_per_beat
        for note_num, data in active_notes.items():
            duration = final_time - data['start_time']
            if duration > 0:
                notes.append({
                    'noteNumber': note_num,
                    'startTime': data['start_time'],
                    'duration': duration,
                    'velocity': float(data['velocity']),
                    'offVelocity': 0.0
                })

        if not notes:
            return {'success': False, 'message': "No valid notes found in MIDI file"}

        # Map original notes to 16 pads: base note 36 + (original - min_note) % 16
        min_note = min(n['noteNumber'] for n in notes)
        mapped_notes = []
        for n in notes:
            pad_index = (n['noteNumber'] - min_note) % 16
            mapped_notes.append({
                'noteNumber': 36 + pad_index,
                'startTime': n['startTime'],
                'duration': n['duration'],
                'velocity': n['velocity'],
                'offVelocity': n['offVelocity']
            })

        # Determine clip length as nearest bar (4 beats)
        max_end = max(n['startTime'] + n['duration'] for n in mapped_notes)
        clip_length = max(4.0, ((int(max_end) // 4) + 1) * 4.0)

        # Load the 808 template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', '808.abl')
        song = load_set_template(template_path)

        # Update the clip
        clip = song['tracks'][0]['clipSlots'][0]['clip']
        clip['notes'] = mapped_notes
        clip['region']['end'] = clip_length
        clip['region']['loop']['end'] = clip_length

        # Update tempo and save
        song['tempo'] = tempo
        output_dir = "/data/UserData/UserLibrary/Sets"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, set_name)
        if not output_path.endswith('.abl'):
            output_path += '.abl'
        with open(output_path, 'w') as f:
            json.dump(song, f, indent=2)

        return {'success': True, 'message': f"Drum set '{set_name}' generated successfully ({len(mapped_notes)} pads)", 'path': output_path}

    except Exception as e:
        return {'success': False, 'message': f"Failed to process drum MIDI file: {str(e)}"}
