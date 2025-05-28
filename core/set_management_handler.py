import os
import json
import copy
import mido
from typing import Dict, List, Any, Optional, Tuple, Set

def analyze_midi_channels(midi_file_path: str) -> Dict[str, Any]:
    """
    Analyze a MIDI file to extract channel information.
    
    Args:
        midi_file_path: Path to the MIDI file
        
    Returns:
        Dictionary containing channel analysis data
    """
    try:
        mid = mido.MidiFile(midi_file_path)
        
        # Dictionary to store channel info
        channels = {}
        
        # GM instrument names (General MIDI standard)
        gm_instruments = [
            "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
            "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavi", "Celesta", "Glockenspiel",
            "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
            "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ",
            "Accordion", "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)",
            "Electric Guitar (jazz)", "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar",
            "Distortion Guitar", "Guitar harmonics", "Acoustic Bass", "Electric Bass (finger)",
            "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1",
            "Synth Bass 2", "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings",
            "Pizzicato Strings", "Orchestral Harp", "Timpani", "String Ensemble 1", "String Ensemble 2",
            "SynthStrings 1", "SynthStrings 2", "Choir Aahs", "Voice Oohs", "Synth Voice",
            "Orchestra Hit", "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn",
            "Brass Section", "SynthBrass 1", "SynthBrass 2", "Soprano Sax", "Alto Sax",
            "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet",
            "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi",
            "Whistle", "Ocarina", "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)",
            "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)",
            "Lead 8 (bass + lead)", "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)",
            "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
            "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
            "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
            "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", "Bag pipe", "Fiddle", "Shanai",
            "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom",
            "Synth Drum", "Reverse Cymbal", "Guitar Fret Noise", "Breath Noise", "Seashore",
            "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"
        ]
        
        # Track program changes per channel
        program_per_channel = {}
        
        # Process all tracks
        for track_idx, track in enumerate(mid.tracks):
            current_time = 0
            current_channel = None
            
            for msg in track:
                current_time += msg.time
                
                # Track program changes
                if msg.type == 'program_change':
                    program_per_channel[msg.channel] = msg.program
                
                # Track note events
                if msg.type in ['note_on', 'note_off']:
                    channel = msg.channel
                    
                    if channel not in channels:
                        channels[channel] = {
                            'channel': channel,
                            'note_count': 0,
                            'min_note': 127,
                            'max_note': 0,
                            'tracks': set(),
                            'program': None,
                            'instrument_name': None
                        }
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        channels[channel]['note_count'] += 1
                        channels[channel]['min_note'] = min(channels[channel]['min_note'], msg.note)
                        channels[channel]['max_note'] = max(channels[channel]['max_note'], msg.note)
                        channels[channel]['tracks'].add(track_idx)
        
        # Add program/instrument info
        for channel, info in channels.items():
            if channel in program_per_channel:
                program = program_per_channel[channel]
                info['program'] = program
                if 0 <= program < len(gm_instruments):
                    info['instrument_name'] = gm_instruments[program]
            
            # Convert tracks set to list for JSON serialization
            info['tracks'] = list(info['tracks'])
        
        # Convert to list and sort by channel number
        channel_list = sorted(channels.values(), key=lambda x: x['channel'])
        
        return {
            'success': True,
            'channels': channel_list,
            'total_channels': len(channel_list)
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to analyze MIDI file: {str(e)}"
        }


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


def generate_midi_set_from_file(set_name: str, midi_file_path: str, tempo: float = None, 
                               selected_channels: Optional[List[int]] = None, 
                               flatten_channels: bool = False) -> Dict[str, Any]:
    """
    Generate an Ableton Live set from an uploaded MIDI file.
    
    Args:
        set_name: Name for the new set
        midi_file_path: Path to the uploaded MIDI file
        tempo: Tempo in BPM (if None, will try to detect from MIDI or use 120)
        selected_channels: List of MIDI channels to include (0-15), None means all channels
        flatten_channels: If True, combine all selected channels into one track
        
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
        
        # Extract notes from MIDI with channel filtering
        notes = []
        ticks_per_beat = mid.ticks_per_beat
        
        # Process all tracks to extract notes
        for track in mid.tracks:
            current_time = 0
            active_notes = {}  # Track active notes by (channel, note_number)
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Check if we should include this channel
                    if selected_channels is None or msg.channel in selected_channels:
                        key = (msg.channel, msg.note)
                        active_notes[key] = {
                            'start_time': current_time / ticks_per_beat,
                            'velocity': msg.velocity,
                            'channel': msg.channel
                        }
                        
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (msg.channel, msg.note)
                    if key in active_notes:
                        start_beat = active_notes[key]['start_time']
                        duration = (current_time / ticks_per_beat) - start_beat
                        
                        # Only add notes with positive duration
                        if duration > 0:
                            notes.append({
                                'noteNumber': msg.note,
                                'startTime': start_beat,
                                'duration': duration,
                                'velocity': float(active_notes[key]['velocity']),
                                'offVelocity': 0.0,
                                'channel': active_notes[key]['channel']
                            })
                        
                        del active_notes[key]
            
            # Handle any remaining active notes in this track
            final_time = current_time / ticks_per_beat
            for key, note_data in active_notes.items():
                duration = final_time - note_data['start_time']
                if duration > 0:
                    notes.append({
                        'noteNumber': key[1],  # note number from key
                        'startTime': note_data['start_time'],
                        'duration': duration,
                        'velocity': float(note_data['velocity']),
                        'offVelocity': 0.0,
                        'channel': note_data['channel']
                    })
        
        if not notes:
            return {
                'success': False,
                'message': "No valid notes found in MIDI file"
            }
        
        # Sort notes by start time
        notes.sort(key=lambda x: x['startTime'])
        
        # Remove channel information from notes (not needed in final output)
        clean_notes = []
        for note in notes:
            clean_note = {
                'noteNumber': note['noteNumber'],
                'startTime': note['startTime'],
                'duration': note['duration'],
                'velocity': note['velocity'],
                'offVelocity': note['offVelocity']
            }
            clean_notes.append(clean_note)
        
        # Calculate clip length (round up to nearest bar)
        max_end_time = max(note['startTime'] + note['duration'] for note in clean_notes)
        clip_length = max(4.0, ((int(max_end_time) // 4) + 1) * 4.0)
        
        # Load the template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl')
        song = load_set_template(template_path)
        
        # Update the clip with MIDI notes
        clip = song['tracks'][0]['clipSlots'][0]['clip']
        clip['notes'] = clean_notes
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
        
        # Create informative message about channel selection
        channel_info = ""
        if selected_channels is not None:
            channel_info = f" from channel(s) {', '.join(str(c) for c in selected_channels)}"
        elif flatten_channels:
            channel_info = " (all channels flattened)"
        
        return {
            'success': True,
            'message': f"MIDI set '{set_name}' generated successfully ({len(clean_notes)} notes imported{channel_info})",
            'path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to process MIDI file: {str(e)}"
        }


# --- Drum set generation from MIDI file ---
def generate_drum_set_from_file(set_name: str, midi_file_path: str, tempo: float = None,
                               selected_channels: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Generate an Ableton Live set from an uploaded drum MIDI file,
    mapping incoming notes to 16 pads starting at MIDI note 36.
    
    Args:
        set_name: Name for the new set
        midi_file_path: Path to the uploaded MIDI file
        tempo: Tempo in BPM (if None, will try to detect from MIDI or use 120)
        selected_channels: List of MIDI channels to include (0-15), None means all channels
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

        # Extract notes from all tracks with channel filtering
        notes = []
        ticks_per_beat = mid.ticks_per_beat
        
        # Process all tracks to extract notes
        for track in mid.tracks:
            current_time = 0
            active_notes = {}  # Track active notes by (channel, note_number)
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Check if we should include this channel
                    if selected_channels is None or msg.channel in selected_channels:
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
                        
                        # Only add notes with positive duration
                        if duration > 0:
                            notes.append({
                                'noteNumber': msg.note,
                                'startTime': start_beat,
                                'duration': duration,
                                'velocity': float(active_notes[key]['velocity']),
                                'offVelocity': 0.0
                            })
                        
                        del active_notes[key]
            
            # Handle any remaining active notes in this track
            final_time = current_time / ticks_per_beat
            for key, note_data in active_notes.items():
                duration = final_time - note_data['start_time']
                if duration > 0:
                    notes.append({
                        'noteNumber': key[1],  # note number from key
                        'startTime': note_data['start_time'],
                        'duration': duration,
                        'velocity': float(note_data['velocity']),
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
