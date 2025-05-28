from handlers.base_handler import BaseHandler
import os
import zipfile
import tempfile
import shutil
from core.set_management_handler import (
    create_set, generate_midi_set_from_file, generate_drum_set_from_file,
    generate_c_major_chord_example, load_set_template, analyze_midi_channels
)
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle
import json

class SetManagementHandler(BaseHandler):
    def _generate_channel_selection_html(self, channels, filename):
        """Generate HTML for channel selection interface."""
        if not channels:
            return '<p>No channels with notes found in this MIDI file.</p>'
        
        html = f'<h3>Channel Selection for: {filename}</h3>'
        html += '<table class="channel-table">'
        html += '<thead><tr><th>Select</th><th>Channel</th><th>Instrument</th><th>Notes</th><th>Note Range</th></tr></thead>'
        html += '<tbody>'
        
        for ch in channels:
            channel_num = ch['channel']
            instrument = ch.get('instrument_name', 'Unknown')
            note_count = ch['note_count']
            min_note = ch['min_note']
            max_note = ch['max_note']
            
            # Convert MIDI note numbers to note names
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            min_note_name = f"{note_names[min_note % 12]}{min_note // 12 - 1}"
            max_note_name = f"{note_names[max_note % 12]}{max_note // 12 - 1}"
            
            html += f'<tr>'
            html += f'<td><input type="checkbox" name="channel_{channel_num}" value="{channel_num}" checked></td>'
            html += f'<td>{channel_num + 1}</td>'  # Display as 1-16 instead of 0-15
            html += f'<td>{instrument}</td>'
            html += f'<td>{note_count}</td>'
            html += f'<td>{min_note_name} - {max_note_name}</td>'
            html += f'</tr>'
        
        html += '</tbody></table>'
        html += '<div class="channel-options">'
        html += '<label><input type="checkbox" name="flatten_channels" value="true"> Flatten all selected channels into one track</label>'
        html += '</div>'
        
        return html
    def handle_get(self):
        """
        Return context for rendering the Set Management page.
        """
        # Get available pads
        _, ids = list_msets(return_free_ids=True)
        free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
        pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in free_pads)
        pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + pad_options
        # Pad color options (1-26)
        pad_color_options = ''.join(f'<option value="{i}">{i}</option>' for i in range(1,27))
        return {
            'pad_options': pad_options,
            'pad_color_options': pad_color_options,
            'channel_selection_html': '',  # Empty by default
            'midi_filepath': ''  # Empty by default
        }

    def handle_post(self, form):
        """
        Handle POST request for set management operations.
        """
        action = form.getvalue('action', 'create')

        # Get pad options for error responses
        _, ids = list_msets(return_free_ids=True)
        free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
        pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in free_pads)
        pad_color_options = ''.join(f'<option value="{i}">{i}</option>' for i in range(1,27))

        if action == 'analyze_midi':
            # Analyze MIDI file channels
            if 'midi_file' not in form:
                return self.format_error_response("No MIDI file uploaded", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
            
            fileitem = form['midi_file']
            if not fileitem.filename:
                return self.format_error_response("No MIDI file selected", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
            
            # Check file extension
            filename = fileitem.filename.lower()
            if not (filename.endswith('.mid') or filename.endswith('.midi')):
                return self.format_error_response("Invalid file type. Please upload a .mid or .midi file", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
            
            # Save uploaded file temporarily
            success, filepath, error_response = self.handle_file_upload(form, 'midi_file')
            if not success:
                return self.format_error_response(error_response.get('message', "Failed to upload MIDI file"), pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
            
            try:
                # Analyze the MIDI file
                analysis_result = analyze_midi_channels(filepath)
                
                if not analysis_result.get('success'):
                    self.cleanup_upload(filepath)
                    return self.format_error_response(analysis_result.get('message', 'Failed to analyze MIDI file'), pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
                
                # Store the filename for later use
                channels = analysis_result.get('channels', [])
                
                # Generate channel selection HTML
                channel_html = self._generate_channel_selection_html(channels, filename)
                
                # Keep the file temporarily - store the path in session
                # We'll pass the filepath as a hidden field instead of cleaning up
                
                return {
                    'message': f"MIDI file analyzed: {len(channels)} channel(s) found",
                    'message_type': 'success',
                    'channel_selection_html': channel_html,
                    'pad_options': pad_options,
                    'pad_color_options': pad_color_options,
                    'filename': filename,
                    'midi_filepath': filepath  # Pass the filepath to the template
                }
                
            except Exception as e:
                # Clean up on error
                self.cleanup_upload(filepath)
                raise
        
        elif action == 'upload_midi':
            # Generate set from uploaded MIDI file
            set_name = form.getvalue('set_name')
            if not set_name:
                return self.format_error_response("Missing required parameter: set_name", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
            
            # Check if we have a filepath from previous analysis
            filepath = form.getvalue('midi_filepath')
            
            if not filepath:
                # Handle file upload if no filepath provided
                if 'midi_file' not in form:
                    return self.format_error_response("No MIDI file uploaded", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
                
                fileitem = form['midi_file']
                if not fileitem.filename:
                    return self.format_error_response("No MIDI file selected", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
                
                # Check file extension
                filename = fileitem.filename.lower()
                if not (filename.endswith('.mid') or filename.endswith('.midi')):
                    return self.format_error_response("Invalid file type. Please upload a .mid or .midi file", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
                
                # Save uploaded file temporarily
                success, filepath, error_response = self.handle_file_upload(form, 'midi_file')
                if not success:
                    return self.format_error_response(error_response.get('message', "Failed to upload MIDI file"), pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
            else:
                # Verify the filepath exists
                if not os.path.exists(filepath):
                    return self.format_error_response("MIDI file no longer exists. Please upload again.", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
            
            try:
                # Get tempo if provided
                tempo_str = form.getvalue('tempo')
                tempo = float(tempo_str) if tempo_str and tempo_str.strip() else None

                # Get selected channels
                selected_channels = []
                flatten_channels = form.getvalue('flatten_channels') == 'true'
                
                # Check for channel selections
                for key in form.keys():
                    if key.startswith('channel_'):
                        try:
                            channel_num = int(form.getvalue(key))
                            selected_channels.append(channel_num)
                        except ValueError:
                            pass
                
                # Dispatch based on MIDI type
                midi_type = form.getvalue('midi_type', 'melodic')
                if midi_type == 'drum':
                    # Pass channel selection to drum MIDI processing
                    if selected_channels:
                        result = generate_drum_set_from_file(set_name, filepath, tempo,
                                                           selected_channels=selected_channels)
                    else:
                        result = generate_drum_set_from_file(set_name, filepath, tempo)
                else:
                    # Pass channel selection to melodic MIDI processing
                    if selected_channels:
                        result = generate_midi_set_from_file(set_name, filepath, tempo, 
                                                           selected_channels=selected_channels,
                                                           flatten_channels=flatten_channels)
                    else:
                        # No channels selected means use all channels
                        result = generate_midi_set_from_file(set_name, filepath, tempo,
                                                           flatten_channels=flatten_channels)

            finally:
                # Clean up uploaded file
                self.cleanup_upload(filepath)

        else:
            return self.format_error_response(f"Unknown action: {action}", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')

        # Check if the operation was successful
        if not result.get('success'):
            return self.format_error_response(result.get('message', 'Operation failed'), pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')

        # Parse pad assignment
        pad_selected = form.getvalue('pad_index')
        pad_color = form.getvalue('pad_color')
        if not pad_selected or not pad_selected.isdigit():
            return self.format_error_response("Invalid pad selection", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
        if not pad_color or not pad_color.isdigit():
            return self.format_error_response("Invalid pad color", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
        pad_selected_int = int(pad_selected) - 1
        pad_color_int = int(pad_color)
        # Prepare bundling of generated set
        set_path = result.get('path')
        if not set_path:
            return self.format_error_response("Internal error: missing set path", pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
        # Create temp directory for bundling
        with tempfile.TemporaryDirectory() as tmpdir:
            song_abl_path = os.path.join(tmpdir, 'Song.abl')
            shutil.copy(set_path, song_abl_path)
            # Name bundle based on set name without .abl extension
            base_path, _ = os.path.splitext(set_path)
            bundle_path = base_path + '.ablbundle'
            with zipfile.ZipFile(bundle_path, 'w') as zf:
                zf.write(song_abl_path, 'Song.abl')
            # Restore to device
            restore_result = restore_ablbundle(bundle_path, pad_selected_int, pad_color_int)
            os.remove(bundle_path)
        
        if restore_result.get('success'):
            # Clean up the original .abl file after successful placement
            try:
                os.remove(set_path)
            except Exception as e:
                print(f"Warning: Failed to clean up set file {set_path}: {e}")
            
            # Refresh pad list after successful placement
            _, updated_ids = list_msets(return_free_ids=True)
            updated_free_pads = sorted([pad_id + 1 for pad_id in updated_ids.get("free", [])])
            updated_pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in updated_free_pads)
            updated_pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + updated_pad_options
            
            return self.format_success_response(restore_result['message'], pad_options=updated_pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
        else:
            return self.format_error_response(restore_result.get('message'), pad_options=pad_options, pad_color_options=pad_color_options, channel_selection_html='', midi_filepath='')
