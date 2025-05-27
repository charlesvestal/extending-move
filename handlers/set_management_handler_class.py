from handlers.base_handler import BaseHandler
import os
import zipfile
import tempfile
import shutil
from core.set_management_handler import (
    create_set, generate_set_from_template,
    get_available_patterns, get_drum_note_mappings
)
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle
import json

class SetManagementHandler(BaseHandler):
    def handle_get(self):
        """
        Return context for rendering the Set Management page.
        """
        patterns = get_available_patterns()
        drum_notes = get_drum_note_mappings()
        # Get available pads
        _, ids = list_msets(return_free_ids=True)
        free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
        print("DEBUG: Free pads found for Set Management:", free_pads)
        import sys; sys.stdout.flush()
        pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in free_pads)
        pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + pad_options
        # Pad color options (1-26)
        pad_color_options = ''.join(f'<option value="{i}">{i}</option>' for i in range(1,27))
        print(f"DEBUG: SetManagementHandler GET - pad_options: {pad_options}")
        import sys; sys.stdout.flush()
        print("DEBUG: SetManagementHandler GET context:", {'patterns': patterns, 'drum_notes': drum_notes, 'pad_options': pad_options, 'pad_color_options': pad_color_options})
        import sys; sys.stdout.flush()
        return {
            'patterns': patterns,
            'drum_notes': drum_notes,
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

        if action == 'create':
            # Original create set functionality
            set_name = form.getvalue('set_name')
            if not set_name:
                return self.format_error_response("Missing required parameter: set_name", pad_options=pad_options, pad_color_options=pad_color_options)
            result = create_set(set_name)

        elif action == 'generate':
            # Generate set with modified note lanes
            set_name = form.getvalue('set_name')
            if not set_name:
                return self.format_error_response("Missing required parameter: set_name", pad_options=pad_options, pad_color_options=pad_color_options)

            # Parse track configurations
            tracks_config = []

            # Get configurations for up to 4 tracks
            for i in range(4):
                track_enabled = form.getvalue(f'track{i}_enabled')
                if track_enabled == 'on':
                    pattern = form.getvalue(f'track{i}_pattern', 'kick')
                    note = int(form.getvalue(f'track{i}_note', '48'))
                    velocity = int(form.getvalue(f'track{i}_velocity', '127'))
                    # Get modifications
                    pitch_shift = int(form.getvalue(f'track{i}_pitch_shift', '0'))
                    velocity_scale = float(form.getvalue(f'track{i}_velocity_scale', '1.0'))
                    time_scale = float(form.getvalue(f'track{i}_time_scale', '1.0'))
                    swing = float(form.getvalue(f'track{i}_swing', '0.0'))
                    track_config = {
                        'pattern': pattern,
                        'note': note,
                        'velocity': velocity,
                        'modifications': {
                            'pitch_shift': pitch_shift,
                            'velocity_scale': velocity_scale,
                            'time_scale': time_scale,
                            'swing': swing
                        }
                    }
                    tracks_config.append(track_config)

            # Generate the set
            result = generate_set_from_template(set_name, tracks_config=tracks_config)

        else:
            return self.format_error_response(f"Unknown action: {action}", pad_options=pad_options, pad_color_options=pad_color_options)

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
            bundle_path = set_path + '.ablbundle'
            with zipfile.ZipFile(bundle_path, 'w') as zf:
                zf.write(song_abl_path, 'Song.abl')
            # Restore to device
            restore_result = restore_ablbundle(bundle_path, pad_selected_int, pad_color_int)
            os.remove(bundle_path)
        if restore_result.get('success'):
            return self.format_success_response(restore_result['message'], pad_options=pad_options, pad_color_options=pad_color_options)
        else:
            return self.format_error_response(restore_result.get('message'), pad_options=pad_options, pad_color_options=pad_color_options)
