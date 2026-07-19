import os
import json
import copy
import math
import re
import mido
from typing import Dict, List, Any, Optional

from core.utils import load_set_template


def sanitize_set_name(set_name: str) -> Optional[str]:
    """Sanitize set_name to prevent path traversal.
    Returns a safe name or None if the name is invalid."""
    if not set_name or not isinstance(set_name, str):
        return None
    # Reject any path separators or traversal attempts
    if '/' in set_name or '\\' in set_name or '..' in set_name:
        return None
    # Allow alphanumeric, spaces, hyphens, underscores
    if not re.match(r'^[\w\s\-]+$', set_name):
        return None
    return set_name

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
        safe_name = sanitize_set_name(set_name)
        if not safe_name:
            return {'success': False, 'message': 'Invalid set name: use only letters, numbers, spaces, hyphens, and underscores'}
        
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
        clip_length = max(4.0, math.ceil(max_end_time / 4.0) * 4.0)
        
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
        safe_name = sanitize_set_name(set_name)
        if not safe_name:
            return {'success': False, 'message': 'Invalid set name: use only letters, numbers, spaces, hyphens, and underscores'}
        
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

        # Determine clip length (round up to nearest bar)
        max_end = max(n['startTime'] + n['duration'] for n in mapped_notes)
        clip_length = max(4.0, math.ceil(max_end / 4.0) * 4.0)

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


def generate_multichannel_midi_set(set_name: str, midi_file_path: str, tempo: float = None) -> Dict[str, Any]:
    """
    Generate an Ableton Live set from a multi-channel MIDI file.
    Each MIDI channel (up to 4) becomes a separate track with its own clip.
    
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
        
        # Extract notes grouped by channel
        ticks_per_beat = mid.ticks_per_beat
        channel_notes = {}  # channel -> list of notes
        
        for track in mid.tracks:
            current_time = 0
            active_notes = {}  # (channel, note) -> start_time
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    key = (msg.channel, msg.note)
                    active_notes[key] = {
                        'start_time': current_time / ticks_per_beat,
                        'velocity': msg.velocity
                    }
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (msg.channel, msg.note)
                    if key in active_notes:
                        start_beat = active_notes[key]['start_time']
                        duration = (current_time / ticks_per_beat) - start_beat
                        
                        if duration > 0:
                            channel = msg.channel
                            if channel not in channel_notes:
                                channel_notes[channel] = []
                            
                            channel_notes[channel].append({
                                'noteNumber': msg.note,
                                'startTime': start_beat,
                                'duration': duration,
                                'velocity': float(active_notes[key]['velocity']),
                                'offVelocity': 0.0
                            })
                        
                        del active_notes[key]
            
            # Handle any remaining active notes at end of track
            final_time = current_time / ticks_per_beat
            for (channel, note_num), data in active_notes.items():
                duration = final_time - data['start_time']
                if duration > 0:
                    if channel not in channel_notes:
                        channel_notes[channel] = []
                    
                    channel_notes[channel].append({
                        'noteNumber': note_num,
                        'startTime': data['start_time'],
                        'duration': duration,
                        'velocity': float(data['velocity']),
                        'offVelocity': 0.0
                    })
        
        # Filter out channels with no notes
        channel_notes = {ch: notes for ch, notes in channel_notes.items() if notes}
        
        if not channel_notes:
            return {'success': False, 'message': "No note data found in MIDI file"}
        
        # Check channel limit
        if len(channel_notes) > 4:
            return {
                'success': False,
                'message': f"MIDI file contains {len(channel_notes)} channels with notes. Maximum supported is 4 channels."
            }
        
        # Load the template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
        song = load_set_template(template_path)
        
        # Calculate clip length based on all notes
        max_end_time = 0
        for notes in channel_notes.values():
            if notes:
                channel_max = max(note['startTime'] + note['duration'] for note in notes)
                max_end_time = max(max_end_time, channel_max)
        
        clip_length = max(4.0, math.ceil(max_end_time / 4.0) * 4.0)
        
        # Get channels sorted
        channels = sorted(channel_notes.keys())
        
        # Assign notes to tracks (up to 4)
        for i, channel in enumerate(channels[:4]):
            notes = channel_notes[channel]
            notes.sort(key=lambda x: x['startTime'])
            
            # Use the i-th track's first clip slot
            if i < len(song['tracks']):
                track = song['tracks'][i]
                if track['clipSlots']:
                    clip = track['clipSlots'][0]['clip']
                    clip['notes'] = notes
                    clip['region']['end'] = clip_length
                    clip['region']['loop']['end'] = clip_length
                    # Name the track based on channel
                    track['name'] = f"Ch {channel + 1}"
        
        # Update tempo
        song['tempo'] = tempo
        
        # Save the modified set
        output_dir = "/data/UserData/UserLibrary/Sets"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, set_name)
        if not output_path.endswith('.abl'):
            output_path += '.abl'
        
        with open(output_path, 'w') as f:
            json.dump(song, f, indent=2)
        
        # Build success message
        channel_summary = ", ".join([f"Ch {ch+1}: {len(notes)} notes" for ch, notes in channel_notes.items()])
        
        return {
            'success': True,
            'message': f"Multi-channel set '{set_name}' generated successfully ({len(channel_notes)} channels - {channel_summary})",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to process multi-channel MIDI file: {str(e)}"
        }


def assign_midi_to_track(set_name: str, midi_file_path: str, target_track: int, 
                         existing_set_path: str = None, tempo: float = None, clip_color: int = None) -> Dict[str, Any]:
    """
    Assign a single-track MIDI file to a specific track slot (1-4) in a set.
    Can create a new set or append to an existing set.
    
    Args:
        set_name: Name for the new set (or name of existing set)
        midi_file_path: Path to the uploaded MIDI file
        target_track: Track number 1-4 to place the MIDI on
        existing_set_path: If provided, load this set and add to it. If None, create new set.
        tempo: Tempo in BPM (if None, will try to detect from MIDI or use 120)
        clip_color: Color ID for new clip (1-9) when adding to existing set
        
    Returns:
        Result dictionary with success status and message
    """
    try:
        safe_name = sanitize_set_name(set_name)
        if not safe_name:
            return {'success': False, 'message': 'Invalid set name: use only letters, numbers, spaces, hyphens, and underscores'}
        
        # Validate track number
        if target_track < 1 or target_track > 4:
            return {
                'success': False,
                'message': f"Invalid track number {target_track}. Must be 1-4."
            }
        
        # Load and parse the MIDI file
        mid = mido.MidiFile(midi_file_path)
        
        # Detect tempo
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
        
        # Extract notes from first track with note data
        ticks_per_beat = mid.ticks_per_beat
        notes = []
        current_time = 0
        active_notes = {}
        
        note_track = None
        for track in mid.tracks:
            has_notes = any(msg.type in ['note_on', 'note_off'] for msg in track)
            if has_notes:
                note_track = track
                break
        
        if note_track is None:
            return {'success': False, 'message': "No note data found in MIDI file"}
        
        for msg in note_track:
            current_time += msg.time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = {
                    'start_time': current_time / ticks_per_beat,
                    'velocity': msg.velocity
                }
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    start_beat = active_notes[msg.note]['start_time']
                    duration = (current_time / ticks_per_beat) - start_beat
                    
                    if duration > 0:
                        notes.append({
                            'noteNumber': msg.note,
                            'startTime': start_beat,
                            'duration': duration,
                            'velocity': float(active_notes[msg.note]['velocity']),
                            'offVelocity': 0.0
                        })
                    
                    del active_notes[msg.note]
        
        # Handle remaining active notes
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
        
        notes.sort(key=lambda x: x['startTime'])
        
        # Calculate clip length
        max_end_time = max(note['startTime'] + note['duration'] for note in notes)
        clip_length = max(4.0, math.ceil(max_end_time / 4.0) * 4.0)
        
        # Load existing set or create new
        template_clip = None
        if existing_set_path and os.path.exists(existing_set_path):
            # Load existing set
            with open(existing_set_path, 'r') as f:
                song = json.load(f)
            mode = "updated"
            # Find an existing clip to use as template for new clips
            for t in song.get('tracks', []):
                for slot in t.get('clipSlots', []):
                    if slot.get('clip') is not None:
                        template_clip = copy.deepcopy(slot['clip'])
                        break
                if template_clip:
                    break
        else:
            # Create new set from template
            template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
            song = load_set_template(template_path)
            # Store a copy of the template's clip structure before clearing
            template_clip = copy.deepcopy(song['tracks'][0]['clipSlots'][0]['clip'])
            # Clear all clips from template
            for track in song.get('tracks', []):
                for slot in track.get('clipSlots', []):
                    slot['clip'] = None
            mode = "created"
        
        # Fallback: load template clip if we didn't find one
        if template_clip is None:
            template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
            tmpl = load_set_template(template_path)
            template_clip = copy.deepcopy(tmpl['tracks'][0]['clipSlots'][0]['clip'])
        
        # Validate track index
        track_idx = target_track - 1  # Convert 1-4 to 0-3
        if track_idx >= len(song['tracks']):
            return {
                'success': False,
                'message': f"Track {target_track} does not exist in set (max {len(song['tracks'])} tracks)"
            }
        
        # Assign notes to target track - find first empty clip slot
        track = song['tracks'][track_idx]
        if track['clipSlots'] and len(track['clipSlots']) > 0:
            # Find first empty clip slot
            empty_slot_idx = None
            for idx, slot in enumerate(track['clipSlots']):
                if slot.get('clip') is None:
                    empty_slot_idx = idx
                    break
            
            if empty_slot_idx is None:
                return {
                    'success': False,
                    'message': f"Track {target_track} has no empty clip slots available"
                }
            
            # Create new clip from template structure with our notes
            new_clip = copy.deepcopy(template_clip)
            new_clip['isPlaying'] = True
            new_clip['name'] = ''
            new_clip['color'] = clip_color if clip_color else 1
            new_clip['isEnabled'] = True
            new_clip['region'] = {'start': 0.0, 'end': clip_length, 'loop': {'start': 0.0, 'end': clip_length, 'isEnabled': True}}
            new_clip['notes'] = notes
            new_clip['stepEditorScrollPosition'] = 0.0
            new_clip['envelopes'] = []
            track['clipSlots'][empty_slot_idx]['clip'] = new_clip
            track['name'] = f"Track {target_track}"
        else:
            return {
                'success': False,
                'message': f"Track {target_track} has no clip slots available"
            }
        
        # Only update tempo when creating new set, preserve existing set's tempo
        if mode == "created":
            song['tempo'] = tempo
        
        # Save - use same path if updating existing set
        if existing_set_path and mode == "updated":
            output_path = existing_set_path
        else:
            # Create new set
            output_dir = "/data/UserData/UserLibrary/Sets"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, set_name)
            if not output_path.endswith('.abl'):
                output_path += '.abl'
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(song, f, indent=2)
        
        return {
            'success': True,
            'message': f"Set '{set_name}' {mode} - Track {target_track} now has {len(notes)} notes",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to assign MIDI to track: {str(e)}"
        }
