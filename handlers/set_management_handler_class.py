from handlers.base_handler import BaseHandler
import os
import zipfile
import tempfile
import shutil
from core.set_management_handler import (
    create_set, generate_midi_set_from_file, generate_c_major_chord_example
)
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle
import json

class SetManagementHandler(BaseHandler):
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
            'pad_color_options': pad_color_options
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

        if action == 'upload_midi':
            # Generate set from uploaded MIDI file
            set_name = form.getvalue('set_name')
            if not set_name:
                return self.format_error_response("Missing required parameter: set_name", pad_options=pad_options, pad_color_options=pad_color_options)
            
            # Handle file upload
            if 'midi_file' not in form:
                return self.format_error_response("No MIDI file uploaded", pad_options=pad_options, pad_color_options=pad_color_options)
            
            fileitem = form['midi_file']
            if not fileitem.filename:
                return self.format_error_response("No MIDI file selected", pad_options=pad_options, pad_color_options=pad_color_options)
            
            # Check file extension
            filename = fileitem.filename.lower()
            if not (filename.endswith('.mid') or filename.endswith('.midi')):
                return self.format_error_response("Invalid file type. Please upload a .mid or .midi file", pad_options=pad_options, pad_color_options=pad_color_options)
            
            # Save uploaded file temporarily
            success, filepath, error_response = self.handle_file_upload(form, 'midi_file')
            if not success:
                return self.format_error_response(error_response.get('message', "Failed to upload MIDI file"), pad_options=pad_options, pad_color_options=pad_color_options)
            
            try:
                # Get tempo if provided
                tempo_str = form.getvalue('tempo')
                tempo = float(tempo_str) if tempo_str and tempo_str.strip() else None
                
                # Process MIDI file
                result = generate_midi_set_from_file(set_name, filepath, tempo)
                
            finally:
                # Clean up uploaded file
                self.cleanup_upload(filepath)

        else:
            return self.format_error_response(f"Unknown action: {action}", pad_options=pad_options, pad_color_options=pad_color_options)

        # Check if the operation was successful
        if not result.get('success'):
            return self.format_error_response(result.get('message', 'Operation failed'), pad_options=pad_options, pad_color_options=pad_color_options)

        # Parse pad assignment
        pad_selected = form.getvalue('pad_index')
        pad_color = form.getvalue('pad_color')
        if not pad_selected or not pad_selected.isdigit():
            return self.format_error_response("Invalid pad selection", pad_options=pad_options, pad_color_options=pad_color_options)
        if not pad_color or not pad_color.isdigit():
            return self.format_error_response("Invalid pad color", pad_options=pad_options, pad_color_options=pad_color_options)
        pad_selected_int = int(pad_selected) - 1
        pad_color_int = int(pad_color)
        # Prepare bundling of generated set
        set_path = result.get('path')
        if not set_path:
            return self.format_error_response("Internal error: missing set path", pad_options=pad_options, pad_color_options=pad_color_options)
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
            
            return self.format_success_response(restore_result['message'], pad_options=updated_pad_options, pad_color_options=pad_color_options)
        else:
            return self.format_error_response(restore_result.get('message'), pad_options=pad_options, pad_color_options=pad_color_options)
