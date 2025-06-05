from handlers.base_handler import BaseHandler
import os
import zipfile
import tempfile
import shutil
import logging
from core.set_management_handler import (
    create_set, generate_midi_set_from_file, generate_drum_set_from_file,
    generate_c_major_chord_example
)
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle
import json

logger = logging.getLogger(__name__)

class SetManagementHandler(BaseHandler):
    def handle_get(self):
        """
        Return context for rendering the MIDI Upload page.
        """
        # Get available pads
        _, ids = list_msets(return_free_ids=True)
        free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
        pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in free_pads)
        pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + pad_options
        pad_color_options = ''.join(f'<option value="{i}">{i}</option>' for i in range(1,27))
        pad_grid = self.generate_pad_grid(ids.get("used", set()))
        return {
            'pad_options': pad_options,
            'pad_color_options': pad_color_options,
            'pad_grid': pad_grid,
            'message': 'Upload a MIDI file to generate a set',
            'message_type': 'info'
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
        pad_grid = self.generate_pad_grid(ids.get("used", set()))

        if action == 'upload_midi':
            # Generate set from uploaded MIDI file
            set_name = form.getvalue('set_name')
            if not set_name:
                return self.format_error_response(
                    "Missing required parameter: set_name",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                )
            
            # Handle file upload
            if 'midi_file' not in form:
                return self.format_error_response(
                    "No MIDI file uploaded",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                )
            
            fileitem = form['midi_file']
            if not fileitem.filename:
                return self.format_error_response(
                    "No MIDI file selected",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                )
            
            # Check file extension
            filename = fileitem.filename.lower()
            if not (filename.endswith('.mid') or filename.endswith('.midi')):
                return self.format_error_response(
                    "Invalid file type. Please upload a .mid or .midi file",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                )
            
            # Save uploaded file temporarily
            success, filepath, error_response = self.handle_file_upload(form, 'midi_file')
            if not success:
                return self.format_error_response(
                    error_response.get('message', "Failed to upload MIDI file"),
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                )
            
            try:
                # Get tempo if provided
                tempo_str = form.getvalue('tempo')
                tempo = float(tempo_str) if tempo_str and tempo_str.strip() else None

                # Dispatch based on MIDI type
                midi_type = form.getvalue('midi_type', 'melodic')
                if midi_type == 'drum':
                    result = generate_drum_set_from_file(set_name, filepath, tempo)
                else:
                    result = generate_midi_set_from_file(set_name, filepath, tempo)

            finally:
                # Clean up uploaded file
                self.cleanup_upload(filepath)

        else:
            return self.format_error_response(
                f"Unknown action: {action}",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
            )

        # Check if the operation was successful
        if not result.get('success'):
            return self.format_error_response(
                result.get('message', 'Operation failed'),
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
            )

        # Parse pad assignment
        pad_selected = form.getvalue('pad_index')
        pad_color = form.getvalue('pad_color')
        if not pad_selected or not pad_selected.isdigit():
            return self.format_error_response(
                "Invalid pad selection",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
            )
        if not pad_color or not pad_color.isdigit():
            return self.format_error_response(
                "Invalid pad color",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
            )
        pad_selected_int = int(pad_selected) - 1
        pad_color_int = int(pad_color)
        # Prepare bundling of generated set
        set_path = result.get('path')
        if not set_path:
            return self.format_error_response(
                "Internal error: missing set path",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
            )
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
                logger.warning("Failed to clean up set file %s: %s", set_path, e)

            # Refresh pad list after successful placement
            _, updated_ids = list_msets(return_free_ids=True)
            updated_free_pads = sorted([pad_id + 1 for pad_id in updated_ids.get("free", [])])
            updated_pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in updated_free_pads)
            updated_pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + updated_pad_options
            pad_grid = self.generate_pad_grid(updated_ids.get("used", set()))
            return self.format_success_response(restore_result['message'], pad_options=updated_pad_options, pad_color_options=pad_color_options, pad_grid=pad_grid)
        else:
            pad_grid = self.generate_pad_grid(ids.get("used", set()))
            return self.format_error_response(restore_result.get('message'), pad_options=pad_options, pad_color_options=pad_color_options, pad_grid=pad_grid)

    def generate_pad_grid(self, used_ids):
        """Return HTML for a 32-pad grid showing occupied pads."""
        cells = []
        # Pad numbering starts with 1 on the bottom-left
        for row in range(3, -1, -1):
            for col in range(8):
                idx = row * 8 + col
                num = idx + 1
                occupied = idx in used_ids
                status = 'occupied' if occupied else 'free'
                disabled = 'disabled' if occupied else ''
                cells.append(
                    f'<input type="radio" id="pad_{num}" name="pad_index" value="{num}" {disabled}>'
                    f'<label for="pad_{num}" class="pad-cell {status}">{num}</label>'
                )
        return '<div class="pad-grid">' + ''.join(cells) + '</div>'
