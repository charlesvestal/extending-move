#!/usr/bin/env python3
import cgi
import urllib.parse
from handlers.base_handler import BaseHandler
from core.drum_rack_inspector_handler import scan_for_drum_rack_presets, get_drum_cell_samples

class DrumRackInspectorHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request for drum rack inspector page."""
        return {
            'options': self.get_preset_options(),
            'message': '',
            'samples_html': ''
        }

    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for preset selection."""
        # Validate action
        valid, error_response = self.validate_action(form, "select_preset")
        if not valid:
            return error_response

        # Get preset path
        preset_path = form.getvalue('preset_select')
        if not preset_path:
            return self.format_error_response("No preset selected")

        try:
            result = get_drum_cell_samples(preset_path)
            if not result['success']:
                return self.format_error_response(result['message'])

            print(f"Found samples: {result['samples']}")  # Debug log
            print("\nProcessing samples for display:")  # Debug log
            # Create a grid container
            samples_html = '<div class="drum-grid">'
            
            # Sort samples by pad number and create a 16-element list (some pads might be empty)
            grid_samples = [None] * 16
            for sample in result['samples']:
                pad_num = int(sample['pad'])
                if 1 <= pad_num <= 16:
                    grid_samples[pad_num - 1] = sample
            
            # Generate grid cells in reverse row order (bottom to top)
            for row in range(3, -1, -1):  # 3,2,1,0 for the four rows
                samples_html += '<div class="drum-grid-row">'
                for col in range(4):  # 0,1,2,3 for the four columns
                    pad_index = row * 4 + col  # Calculate index in grid_samples
                    pad_num = pad_index + 1  # Actual pad number (1-16)
                    
                    sample = grid_samples[pad_index]
                    cell_html = '<div class="drum-cell">'
                    
                    if sample:
                        print(f"\nSample: {sample}")  # Debug log
                        if sample.get('path') and sample['path'].startswith('/data/UserData/UserLibrary/Samples/'):
                            web_path = '/samples/' + sample['path'].replace('/data/UserData/UserLibrary/Samples/Preset Samples/', '', 1)
                            web_path = urllib.parse.quote(web_path)
                            waveform_id = f'waveform-{pad_num}'
                            cell_html += f'''
                                <div class="pad-info">
                                    <span class="pad-number">Pad {pad_num}</span>
                                    <span class="sample-name">{sample["sample"]}</span>
                                    <a href="{web_path}" target="_blank" class="download-link">Download</a>
                                </div>
                                <div id="{waveform_id}" class="waveform-container" data-audio-path="{web_path}"></div>
                            '''
                        else:
                            cell_html += f'<div class="pad-info"><span class="pad-number">Pad {pad_num}</span><span>No sample</span></div>'
                    else:
                        cell_html += f'<div class="pad-info"><span class="pad-number">Pad {pad_num}</span><span>Empty</span></div>'
                    
                    cell_html += '</div>'
                    samples_html += cell_html
                
                samples_html += '</div>'
            
            samples_html += '</div>'

            return {
                'options': self.get_preset_options(),
                'message': result['message'],
                'samples_html': samples_html  # Changed from 'samples' to 'samples_html'
            }

        except Exception as e:
            return self.format_error_response(f"Error processing preset: {str(e)}")

    def get_preset_options(self):
        """Get preset options for the template."""
        try:
            result = scan_for_drum_rack_presets()
            if not result['success']:
                return ''
            options_html = ['<option value="">--Select a Preset--</option>']
            for preset in result['presets']:
                options_html.append(f'<option value="{preset["path"]}">{preset["name"]}</option>')
            return '\n'.join(options_html)
        except Exception as e:
            print(f"Error getting preset options: {e}")
            return ''
