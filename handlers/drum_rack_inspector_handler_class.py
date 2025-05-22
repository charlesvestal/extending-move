#!/usr/bin/env python3
import cgi
import os
import urllib.parse
from handlers.base_handler import BaseHandler
from core.drum_rack_inspector_handler import scan_for_drum_rack_presets, get_drum_cell_samples, update_drum_cell_sample
from core.reverse_handler import reverse_wav_file
from core.refresh_handler import refresh_library
from core.time_stretch_handler import time_stretch_wav

class DrumRackInspectorHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request for drum rack inspector page."""
        return {
            'options': self.get_preset_options(),
            'message': '',
            'samples_html': ''
        }

    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for preset selection and sample operations."""
        # Get action
        action = form.getvalue('action')
        if action == 'reverse_sample':
            return self.handle_reverse_sample(form)
        if action == 'time_stretch_sample':
            return self.handle_time_stretch_sample(form)    
        # Validate preset selection action
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
                            # Add new data-playback-start and data-playback-length attributes
                            cell_html += f'''
                                <div class="pad-info">
                                    <span class="pad-number">Pad {pad_num}</span>
                                </div>
                                <div id="{waveform_id}" class="waveform-container"
                                     data-audio-path="{web_path}"
                                     data-playback-start="{sample.get('playback_start', 0.0)}"
                                     data-playback-length="{sample.get('playback_length', 1.0)}"></div>
                                <div class="sample-info">
                                    <div class="sample-header">
                                        <span class="sample-name">{sample["sample"]}</span>
                                        <a href="{web_path}" target="_blank" class="download-link" aria-label="Download">
                                            <svg fill="none" viewBox="0 0 20 18" height="18" width="20" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M10 12.2892V0M10 12.2892L14.6667 8.19277M10 12.2892L5.33333 8.19277M17 17H3" stroke="currentColor" stroke-width="1.5"/>
                                            </svg>
                                        </a>
                                    </div>
                                    <div class="sample-actions">
                                        <form method="POST" action="/drum-rack-inspector" style="display: inline;">
                                            <input type="hidden" name="action" value="reverse_sample">
                                            <input type="hidden" name="sample_path" value="{sample['path']}">
                                            <input type="hidden" name="preset_path" value="{preset_path}">
                                            <input type="hidden" name="pad_number" value="{pad_num}">
                                            <button type="submit" class="reverse-button">Reverse</button>
                                        </form>
                                        <button type="button" class="time-stretch-button"
                                            data-sample-path="{sample['path']}"
                                            data-preset-path="{preset_path}"
                                            data-pad-number="{pad_num}"
                                            onclick="
                                              var modal = document.getElementById('timeStretchModal');
                                              document.getElementById('ts_sample_path').value = this.getAttribute('data-sample-path');
                                              document.getElementById('ts_preset_path').value = this.getAttribute('data-preset-path');
                                              document.getElementById('ts_pad_number').value = this.getAttribute('data-pad-number');
                                              modal.classList.remove('hidden');
                                            ">
                                            Time Stretch
                                        </button>
                                    </div>
                                </div>
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
    
    def handle_time_stretch_sample(self, form: cgi.FieldStorage):
        """Handle time-stretch action."""
        sample_path = form.getvalue('sample_path')
        preset_path = form.getvalue('preset_path')
        pad_number = form.getvalue('pad_number')
        bpm = form.getvalue('bpm')
        measures = form.getvalue('measures')

        # Step 1: Ask for BPM and measures if not provided
        if bpm is None or measures is None:
            samples_html = f'''
                <div class="time-stretch-form">
                    <form method="POST" action="/drum-rack-inspector">
                        <input type="hidden" name="action" value="time_stretch_sample">
                        <input type="hidden" name="sample_path" value="{sample_path}">
                        <input type="hidden" name="preset_path" value="{preset_path}">
                        <input type="hidden" name="pad_number" value="{pad_number}">
                        <label for="bpm">BPM:</label>
                        <input type="number" name="bpm" id="bpm" step="0.1" required>
                        <label for="measures">Measures:</label>
                        <input type="number" name="measures" id="measures" step="0.1" required>
                        <button type="submit" class="apply-time-stretch-button">Apply Time Stretch</button>
                    </form>
                </div>
            '''
            return {
                'options': self.get_preset_options(),
                'message': '',
                'samples_html': samples_html
            }

        # Step 2: Compute target duration
        try:
            bpm_val = float(bpm)
            measures_val = float(measures)
            # 4 beats per measure, each beat is 60/bpm seconds
            target_duration = (60.0 / bpm_val) * 4 * measures_val
        except ValueError:
            return self.format_error_response("Invalid BPM or measures values")

        # Step 3: Time-stretch the file and update the preset
        import os
        sample_dir = os.path.dirname(sample_path)
        sample_basename = os.path.splitext(os.path.basename(sample_path))[0]
        # Format BPM and measures as strings preserving decimals
        bpm_str = f"{bpm_val:g}"
        measures_str = f"{measures_val:g}"
        output_filename = f"{sample_basename}-stretched-{bpm_str}-{measures_str}.wav"
        # output_filename = f"{sample_basename}-stretched-{int(bpm_val)}-{int(measures_val)}.wav"
        output_path = os.path.join(sample_dir, output_filename)

        success, ts_message, new_path = time_stretch_wav(sample_path, target_duration, output_path)
        if not success:
            return self.format_error_response(f"Failed to time-stretch sample: {ts_message}")

        # Update the preset to use the new time-stretched sample
        update_success, update_message = update_drum_cell_sample(preset_path, pad_number, new_path)
        if not update_success:
            return self.format_error_response(f"Failed to update preset: {update_message}")

        # Show success message and redisplay updated grid
        result = get_drum_cell_samples(preset_path)
        if not result['success']:
            return self.format_error_response(result['message'])

        samples_html = '<div class="drum-grid">'
        grid_samples = [None] * 16
        for sample in result['samples']:
            num = int(sample['pad'])
            if 1 <= num <= 16:
                grid_samples[num - 1] = sample

        for row in range(3, -1, -1):
            samples_html += '<div class="drum-grid-row">'
            for col in range(4):
                idx = row * 4 + col
                num = idx + 1
                sample = grid_samples[idx]
                cell_html = '<div class="drum-cell">'

                if sample and sample.get('path', '').startswith('/data/UserData/UserLibrary/Samples/'):
                    web_path = '/samples/' + sample['path'] \
                                .replace('/data/UserData/UserLibrary/Samples/Preset Samples/', '', 1)
                    web_path = urllib.parse.quote(web_path)
                    wf_id = f'waveform-{num}'
                    cell_html += f'''
                        <div class="pad-info">
                            <span class="pad-number">Pad {num}</span>
                        </div>
                        <div id="{wf_id}" class="waveform-container"
                             data-audio-path="{web_path}"
                             data-playback-start="{sample.get('playback_start', 0.0)}"
                             data-playback-length="{sample.get('playback_length', 1.0)}"></div>
                        <div class="sample-info">
                            <div class="sample-header">
                                <span class="sample-name">{sample["sample"]}</span>
                                <a href="{web_path}" target="_blank" class="download-link" aria-label="Download">
                                    <svg fill="none" viewBox="0 0 20 18" height="18" width="20" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M10 12.2892V0M10 12.2892L14.6667 8.19277M10 12.2892L5.33333 8.19277M17 17H3" stroke="currentColor" stroke-width="1.5"/>
                                    </svg>
                                </a>
                            </div>
                            <div class="sample-actions">
                                <form method="POST" action="/drum-rack-inspector" style="display: inline;">
                                    <input type="hidden" name="action" value="reverse_sample">
                                    <input type="hidden" name="sample_path" value="{sample['path']}">
                                    <input type="hidden" name="preset_path" value="{preset_path}">
                                    <input type="hidden" name="pad_number" value="{num}">
                                    <button type="submit" class="reverse-button">Reverse</button>
                                </form>
                                <button type="button" class="time-stretch-button"
                                    data-sample-path="{sample['path']}"
                                    data-preset-path="{preset_path}"
                                    data-pad-number="{num}"
                                    onclick="
                                      var modal = document.getElementById('timeStretchModal');
                                      document.getElementById('ts_sample_path').value = this.getAttribute('data-sample-path');
                                      document.getElementById('ts_preset_path').value = this.getAttribute('data-preset-path');
                                      document.getElementById('ts_pad_number').value = this.getAttribute('data-pad-number');
                                      modal.classList.remove('hidden');
                                    ">
                                    Time Stretch
                                </button>
                            </div>
                        </div>
                    '''
                elif sample:
                    cell_html += f'<div class="pad-info"><span class="pad-number">Pad {num}</span><span>No sample</span></div>'
                else:
                    cell_html += f'<div class="pad-info"><span class="pad-number">Pad {num}</span><span>Empty</span></div>'

                cell_html += '</div>'
                samples_html += cell_html

            samples_html += '</div>'

        samples_html += '</div>'

        return {
            'options': self.get_preset_options(),
            'message': f"Time-stretched sample created and loaded for pad {pad_number}! {ts_message} {update_message}",
            'samples_html': samples_html
        }
    def handle_reverse_sample(self, form):
        """Handle reversing a sample."""
        sample_path = form.getvalue('sample_path')
        preset_path = form.getvalue('preset_path')
        
        if not sample_path or not preset_path:
            return self.format_error_response("Missing sample or preset path")
            
        try:
            # Get the directory and filename
            sample_dir = os.path.dirname(sample_path)
            sample_filename = os.path.basename(sample_path)
            
            # Reverse the sample
            success, message, new_path = reverse_wav_file(sample_filename, sample_dir)
            if not success:
                return self.format_error_response(f"Failed to reverse sample: {message}")
                
            # Update the preset to use the new sample path
            pad_number = form.getvalue('pad_number')
            if not pad_number:
                return self.format_error_response("Missing pad number")
                
            success, update_message = update_drum_cell_sample(preset_path, pad_number, new_path)
            if not success:
                return self.format_error_response(f"Failed to update preset: {update_message}")
                
            message = f"{message}\n{update_message}"
                
            # Now get the samples to redisplay the grid
            result = get_drum_cell_samples(preset_path)
            if not result['success']:
                return self.format_error_response(result['message'])
                
            # Generate grid HTML
            samples_html = '<div class="drum-grid">'
            grid_samples = [None] * 16
            for sample in result['samples']:
                pad_num = int(sample['pad'])
                if 1 <= pad_num <= 16:
                    grid_samples[pad_num - 1] = sample

            for row in range(3, -1, -1):
                samples_html += '<div class="drum-grid-row">'
                for col in range(4):
                    pad_index = row * 4 + col
                    pad_num = pad_index + 1

                    sample = grid_samples[pad_index]
                    cell_html = '<div class="drum-cell">'

                    if sample:
                        if sample.get('path') and sample['path'].startswith('/data/UserData/UserLibrary/Samples/'):
                            web_path = '/samples/' + sample['path'].replace('/data/UserData/UserLibrary/Samples/Preset Samples/', '', 1)
                            web_path = urllib.parse.quote(web_path)
                            waveform_id = f'waveform-{pad_num}'
                            cell_html += f'''
                                <div class="pad-info">
                                    <span class="pad-number">Pad {pad_num}</span>
                                </div>
                                <div id="{waveform_id}" class="waveform-container"
                                     data-audio-path="{web_path}"
                                     data-playback-start="{sample.get('playback_start', 0.0)}"
                                     data-playback-length="{sample.get('playback_length', 1.0)}"></div>
                                <div class="sample-info">
                                    <div class="sample-header">
                                        <span class="sample-name">{sample["sample"]}</span>
                                        <a href="{web_path}" target="_blank" class="download-link" aria-label="Download">
                                            <svg fill="none" viewBox="0 0 20 18" height="18" width="20" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M10 12.2892V0M10 12.2892L14.6667 8.19277M10 12.2892L5.33333 8.19277M17 17H3" stroke="currentColor" stroke-width="1.5"/>
                                            </svg>
                                        </a>
                                    </div>
                                    <div class="sample-actions">
                                        <form method="POST" action="/drum-rack-inspector" style="display: inline;">
                                            <input type="hidden" name="action" value="reverse_sample">
                                            <input type="hidden" name="sample_path" value="{sample['path']}">
                                            <input type="hidden" name="preset_path" value="{preset_path}">
                                            <input type="hidden" name="pad_number" value="{pad_num}">
                                            <button type="submit" class="reverse-button">Reverse</button>
                                        </form>
                                        <button type="button" class="time-stretch-button"
                                            data-sample-path="{sample['path']}"
                                            data-preset-path="{preset_path}"
                                            data-pad-number="{pad_num}"
                                            onclick="
                                              var modal = document.getElementById('timeStretchModal');
                                              document.getElementById('ts_sample_path').value = this.getAttribute('data-sample-path');
                                              document.getElementById('ts_preset_path').value = this.getAttribute('data-preset-path');
                                              document.getElementById('ts_pad_number').value = this.getAttribute('data-pad-number');
                                              modal.classList.remove('hidden');
                                            ">
                                            Time Stretch
                                        </button>
                                    </div>
                                </div>
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
                'message': message,
                'samples_html': samples_html
            }
            
        except Exception as e:
            return self.format_error_response(f"Error reversing sample: {str(e)}")
