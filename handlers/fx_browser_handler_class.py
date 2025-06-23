import os
import json
from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.fx_browser_handler import extract_fx_parameters

# Base directory for factory presets (read-only)
CORE_LIBRARY_DIR = "/data/CoreLibrary/Audio Effects"

class FxBrowserHandler(BaseHandler):
    """Handler for browsing audio effect presets and chains."""

    def handle_get(self):
        base_dir = "/data/UserData/UserLibrary/Audio Effects"
        if not os.path.exists(base_dir) and os.path.exists("examples/Audio Effects"):
            base_dir = "examples/Audio Effects"
        browser_html = generate_dir_html(
            base_dir,
            "",
            "/fx-browser",
            "preset_select",
            "select_preset",
            filter_key="audiofx",
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith("</ul>"):
            browser_html = browser_html[:-5] + core_li + "</ul>"
        return {
            "message": "Select an effect preset or chain",
            "message_type": "info",
            "file_browser_html": browser_html,
            "params_html": "",
            "selected_preset": None,
            "browser_root": base_dir,
            "browser_filter": "audiofx",
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        if action == "reset_preset":
            return self.handle_get()
        valid, err = self.validate_action(form, "select_preset")
        if not valid:
            return err
        preset_path = form.getvalue("preset_select")
        if not preset_path:
            return self.format_error_response("No preset selected")
        try:
            result = extract_fx_parameters(preset_path)
            if not result["success"]:
                return self.format_error_response(result["message"])
            params_html = self.generate_params_html(result["device"])
            base_dir = "/data/UserData/UserLibrary/Audio Effects"
            if not os.path.exists(base_dir) and os.path.exists("examples/Audio Effects"):
                base_dir = "examples/Audio Effects"
            browser_html = generate_dir_html(
                base_dir,
                "",
                "/fx-browser",
                "preset_select",
                "select_preset",
                filter_key="audiofx",
            )
            core_li = (
                '<li class="dir closed" data-path="Core Library">'
                '<span>📁 Core Library</span>'
                '<ul class="hidden"></ul></li>'
            )
            if browser_html.endswith("</ul>"):
                browser_html = browser_html[:-5] + core_li + "</ul>"
            return {
                "message": result["message"],
                "message_type": "success",
                "file_browser_html": browser_html,
                "params_html": params_html,
                "selected_preset": preset_path,
                "browser_root": base_dir,
                "browser_filter": "audiofx",
            }
        except Exception as exc:
            return self.format_error_response(f"Error processing preset: {exc}")

    def generate_params_html(self, device, depth=0):
        indent = depth * 20
        html = f'<div class="fx-device" style="margin-left:{indent}px">'
        html += f'<h4>{device.get("kind", "device")}</h4>'
        html += '<ul>'
        for name, val in device.get("parameters", {}).items():
            html += f'<li>{name}: {val}</li>'
        html += '</ul>'
        for child in device.get("children", []):
            html += self.generate_params_html(child, depth + 1)
        html += '</div>'
        return html
