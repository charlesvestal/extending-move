from handlers.base_handler import BaseHandler
from core.set_management_handler import (
    create_set, generate_set_from_template, 
    get_available_patterns, get_drum_note_mappings
)
import json

class SetManagementHandler(BaseHandler):
    def handle_get(self):
        """
        Return context for rendering the Set Management page.
        """
        return {
            'patterns': get_available_patterns(),
            'drum_notes': get_drum_note_mappings()
        }

    def handle_post(self, form):
        """
        Handle POST request for set management operations.
        """
        action = form.getvalue('action', 'create')
        
        if action == 'create':
            # Original create set functionality
            set_name = form.getvalue('set_name')
            if not set_name:
                return self.format_error_response("Missing required parameter: set_name")
            result = create_set(set_name)
            
        elif action == 'generate':
            # Generate set with modified note lanes
            set_name = form.getvalue('set_name')
            if not set_name:
                return self.format_error_response("Missing required parameter: set_name")
            
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
            return self.format_error_response(f"Unknown action: {action}")
        
        if result['success']:
            return self.format_success_response(result['message'])
        else:
            return self.format_error_response(result['message'])
