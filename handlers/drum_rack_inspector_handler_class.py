#!/usr/bin/env python3
import os
import urllib.parse
import logging
from core.file_browser import generate_dir_html
from handlers.base_handler import BaseHandler
from core.drum_rack_inspector_handler import (
    get_drum_cell_samples,
    update_drum_cell_sample,
    find_original_sample,
)
from core.reverse_handler import reverse_wav_file
from core.refresh_handler import refresh_library
from core.time_stretch_handler import time_stretch_wav

logger = logging.getLogger(__name__)

class DrumRackInspectorHandler(BaseHandler):
    def handle_get(self):
        """Return file browser HTML for drum rack presets."""
        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/drum-rack-inspector',
            'preset_select',
            'select_preset',
            filter_key='drumrack'
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        return {
            'file_browser_html': browser_html,
            'message': '',
            'samples_html': '',
            'selected_preset': None,
            'browser_root': base_dir,
            'browser_filter': 'drumrack',
            'message_type': 'info',
        }

    def handle_post(self, form):
        """Handle POST request for preset selection and sample operations."""
        # Get action
        action = form.getvalue('action')
        if action == 'reset_preset':
            return self.handle_get()
        if action == 'reverse_sample':
            return self.handle_reverse_sample(form)
        if action == 'time_stretch_sample':
            return self.handle_time_stretch_sample(form)
        if action == 'revert_sample':
            return self.handle_revert_sample(form)
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

            logger.debug("Found samples: %s", result['samples'])
            samples_html = self.generate_samples_html(result['samples'], preset_path)

            base_dir = "/data/UserData/UserLibrary/Track Presets"
            if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
                base_dir = "examples/Track Presets"
            browser_html = generate_dir_html(
                base_dir,
                "",
                '/drum-rack-inspector',
                'preset_select',
                'select_preset',
                filter_key='drumrack'
            )
            core_li = (
                '<li class="dir closed" data-path="Core Library">'
                '<span>📁 Core Library</span>'
                '<ul class="hidden"></ul></li>'
            )
            if browser_html.endswith('</ul>'):
                browser_html = browser_html[:-5] + core_li + '</ul>'

            return {
                'file_browser_html': browser_html,
                'message': result['message'],
                'samples_html': samples_html,
                'selected_preset': preset_path,
                'browser_root': base_dir,
                'browser_filter': 'drumrack',
                'message_type': 'success',
            }

        except Exception as e:
            return self.format_error_response(f"Error processing preset: {str(e)}")

    def get_preset_options(self):
        """Deprecated dropdown helper."""
        return ''

    def generate_samples_html(self, samples, preset_path):
        """Build the drum pad grid HTML."""
        html = '<div class="drum-grid">'
        grid = [None] * 16
        for s in samples:
            idx = int(s['pad'])
            if 1 <= idx <= 16:
                grid[idx - 1] = s

        for row in range(3, -1, -1):
            html += '<div class="drum-grid-row">'
            for col in range(4):
                pad_index = row * 4 + col
                pad_num = pad_index + 1
                sample = grid[pad_index]
                cell = '<div class="drum-cell">'
                if sample and sample.get('path'):
                    path = sample['path']
                    if path.startswith('/data/UserData/UserLibrary/'):
                        rel = path[len('/data/UserData/UserLibrary/') :]
                        web_path = '/files/user-library/' + rel
                    elif path.startswith('/data/CoreLibrary/'):
                        rel = path[len('/data/CoreLibrary/') :]
                        web_path = '/files/core-library/' + rel
                    else:
                        web_path = '/files/user-library/' + path.lstrip('/')
                    web_path = urllib.parse.quote(web_path)
                    wf_id = f'waveform-{pad_num}'
                    cell += f'''<div class="pad-info"><span class="pad-number">Pad {pad_num}</span></div>
                        <div id="{wf_id}" class="waveform-container" data-audio-path="{web_path}" data-playback-start="{sample.get('playback_start', 0.0)}" data-playback-length="{sample.get('playback_length', 1.0)}"></div>
                        <div class="sample-info">
                          <div class="sample-header">
                            <span class="sample-name">{sample['sample']}</span>
                            <a href="{web_path}" target="_blank" class="download-link" aria-label="Download">
                              <svg fill="none" viewBox="0 0 20 18" height="18" width="20" xmlns="http://www.w3.org/2000/svg">
                                <path d="M10 12.2892V0M10 12.2892L14.6667 8.19277M10 12.2892L5.33333 8.19277M17 17H3" stroke="currentColor" stroke-width="1.5"/>
                              </svg>
                            </a>'''
                    original = find_original_sample(sample['path'])
                    if original and original != sample['path']:
                        cell += f'''<form method="POST" action="/drum-rack-inspector" style="display:inline;">
                                    <input type="hidden" name="action" value="revert_sample">
                                    <input type="hidden" name="sample_path" value="{sample['path']}">
                                    <input type="hidden" name="preset_path" value="{preset_path}">
                                    <input type="hidden" name="pad_number" value="{pad_num}">
                                    <button type="submit" class="revert-button" title="Revert to original sample">🔙</button>
                                  </form>'''
                    cell += '''
                          </div>
                          <div class="sample-actions">'''
                    cell += f'''<form method="POST" action="/drum-rack-inspector" style="display:inline;">
                                <input type="hidden" name="action" value="reverse_sample">
                                <input type="hidden" name="sample_path" value="{sample['path']}">
                                <input type="hidden" name="preset_path" value="{preset_path}">
                                <input type="hidden" name="pad_number" value="{pad_num}">
                                <button type="submit" class="reverse-button">Reverse</button>
                              </form>'''
                    cell += f'''<button type="button" class="time-stretch-button" data-sample-path="{sample['path']}" data-preset-path="{preset_path}" data-pad-number="{pad_num}" onclick="var modal = document.getElementById('timeStretchModal'); document.getElementById('ts_sample_path').value = this.getAttribute('data-sample-path'); document.getElementById('ts_preset_path').value = this.getAttribute('data-preset-path'); document.getElementById('ts_pad_number').value = this.getAttribute('data-pad-number'); modal.classList.remove('hidden');">Time Stretch</button>'''
                    cell += '</div></div>'
                elif sample:
                    cell += f'<div class="pad-info"><span class="pad-number">Pad {pad_num}</span><span>No sample</span></div>'
                else:
                    cell += f'<div class="pad-info"><span class="pad-number">Pad {pad_num}</span><span>Empty</span></div>'
                cell += '</div>'
                html += cell
            html += '</div>'
        html += '</div>'
        return html
    
    def handle_time_stretch_sample(self, form):
        """Handle time-stretch action."""
        sample_path = form.getvalue('sample_path')
        preset_path = form.getvalue('preset_path')
        pad_number = form.getvalue('pad_number')
        bpm = form.getvalue('bpm')
        measures = form.getvalue('measures')
        preserve_pitch = form.getvalue('preserve_pitch') is not None
        algorithm = form.getvalue('algorithm') or 'rubberband'

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
            base_dir = "/data/UserData/UserLibrary/Track Presets"
            if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
                base_dir = "examples/Track Presets"
            browser_html = generate_dir_html(
                base_dir,
                "",
                '/drum-rack-inspector',
                'preset_select',
                'select_preset',
                filter_key='drumrack'
            )
            core_li = (
                '<li class="dir closed" data-path="Core Library">'
                '<span>📁 Core Library</span>'
                '<ul class="hidden"></ul></li>'
            )
            if browser_html.endswith('</ul>'):
                browser_html = browser_html[:-5] + core_li + '</ul>'
            return {
                'file_browser_html': browser_html,
                'message': '',
                'samples_html': samples_html,
                'selected_preset': preset_path,
                'browser_root': base_dir,
                'browser_filter': 'drumrack',
                'message_type': 'info',
            }

        # Step 2: Compute target duration
        try:
            bpm_val = float(bpm)
            measures_val = float(measures)
            # 4 beats per measure, each beat is 60/bpm seconds
            target_duration = (60.0 / bpm_val) * 4 * measures_val

            # Retrieve original slice parameters for this pad
            samples_info = get_drum_cell_samples(preset_path)
            if not samples_info['success']:
                return self.format_error_response(samples_info['message'])
            orig = next((s for s in samples_info['samples']
                         if int(s['pad']) == int(pad_number)), None)
            playback_length = float(orig.get('playback_length', 1.0)) if orig else 1.0

            # Compute full-stretch duration so slice maps to target duration
            full_stretch_duration = target_duration / playback_length
        except ValueError:
            return self.format_error_response("Invalid BPM or measures values")

        # Step 3: Time-stretch the file and update the preset
        import os
        sample_dir = os.path.dirname(sample_path)
        sample_basename = os.path.splitext(os.path.basename(sample_path))[0]
        # Format BPM and measures as strings preserving decimals
        bpm_str = f"{bpm_val:g}"
        measures_str = f"{measures_val:g}"
        suffix = 'stretched' if preserve_pitch else 'repitched'
        output_filename = f"{sample_basename}-slice{pad_number}-{suffix}-{bpm_str}-{measures_str}.wav"
        output_path = os.path.join(sample_dir, output_filename)

        success, ts_message, new_path = time_stretch_wav(
            sample_path,
            full_stretch_duration,
            output_path,
            preserve_pitch=preserve_pitch,
            algorithm=algorithm
        )
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

        samples_html = self.generate_samples_html(result['samples'], preset_path)

        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/drum-rack-inspector',
            'preset_select',
            'select_preset',
            filter_key='drumrack'
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        return {
            'file_browser_html': browser_html,
            'message': f"Time-stretched sample created and loaded for pad {pad_number}! {ts_message} {update_message}",
            'samples_html': samples_html,
            'selected_preset': preset_path,
            'browser_root': base_dir,
            'browser_filter': 'drumrack',
            'message_type': 'success',
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

            # Retrieve original slice parameters
            pad_number = form.getvalue('pad_number')
            if not pad_number:
                return self.format_error_response("Missing pad number")
            samples_info = get_drum_cell_samples(preset_path)
            if not samples_info['success']:
                return self.format_error_response(samples_info['message'])
            orig = next((s for s in samples_info['samples'] if int(s['pad']) == int(pad_number)), None)
            if orig:
                orig_start = float(orig.get('playback_start', 0.0))
                orig_length = float(orig.get('playback_length', 1.0))
            else:
                orig_start, orig_length = 0.0, 1.0

            # Reverse the sample
            success, message, new_path = reverse_wav_file(sample_filename, sample_dir)
            if not success:
                return self.format_error_response(f"Failed to reverse sample: {message}")

            # Compute new slice start for reversed audio
            new_start = max(0.0, 1.0 - (orig_start + orig_length))
            new_length = orig_length

            # Update the preset to use the new sample path and new slice parameters
            success, update_message = update_drum_cell_sample(
                preset_path, pad_number, new_path,
                new_playback_start=new_start, new_playback_length=new_length
            )
            if not success:
                return self.format_error_response(f"Failed to update preset: {update_message}")

            message = f"{message}\n{update_message}"

            # Now get the samples to redisplay the grid
            result = get_drum_cell_samples(preset_path)
            if not result['success']:
                return self.format_error_response(result['message'])

            samples_html = self.generate_samples_html(result['samples'], preset_path)

            base_dir = "/data/UserData/UserLibrary/Track Presets"
            if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
                base_dir = "examples/Track Presets"
            browser_html = generate_dir_html(
                base_dir,
                "",
                '/drum-rack-inspector',
                'preset_select',
                'select_preset',
                filter_key='drumrack'
            )
            core_li = (
                '<li class="dir closed" data-path="Core Library">'
                '<span>📁 Core Library</span>'
                '<ul class="hidden"></ul></li>'
            )
            if browser_html.endswith('</ul>'):
                browser_html = browser_html[:-5] + core_li + '</ul>'
            return {
                'file_browser_html': browser_html,
                'message': message,
                'samples_html': samples_html,
                'selected_preset': preset_path,
                'browser_root': base_dir,
                'browser_filter': 'drumrack',
                'message_type': 'success',
            }

        except Exception as e:
            return self.format_error_response(f"Error reversing sample: {str(e)}")

    def handle_revert_sample(self, form):
        """Revert a pad to its original sample if available."""
        sample_path = form.getvalue('sample_path')
        preset_path = form.getvalue('preset_path')
        pad_number = form.getvalue('pad_number')
        if not sample_path or not preset_path or not pad_number:
            return self.format_error_response("Missing parameters")

        original = find_original_sample(sample_path)
        if not original or original == sample_path:
            return self.format_error_response("Original sample not found")

        success, message = update_drum_cell_sample(preset_path, pad_number, original)
        if not success:
            return self.format_error_response(f"Failed to update preset: {message}")

        result = get_drum_cell_samples(preset_path)
        if not result['success']:
            return self.format_error_response(result['message'])

        samples_html = self.generate_samples_html(result['samples'], preset_path)

        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/drum-rack-inspector',
            'preset_select',
            'select_preset',
            filter_key='drumrack'
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        return {
            'file_browser_html': browser_html,
            'message': 'Reverted to original sample',
            'samples_html': samples_html,
            'selected_preset': preset_path,
            'browser_root': base_dir,
            'browser_filter': 'drumrack',
            'message_type': 'success',
        }
