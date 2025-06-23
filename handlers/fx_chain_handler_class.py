#!/usr/bin/env python3
import os
import json
import shutil
import logging

from handlers.base_handler import BaseHandler
from core.effect_chain_handler import extract_effect_parameters, apply_macro_mappings
from core.file_browser import generate_dir_html
from core.refresh_handler import refresh_library

logger = logging.getLogger(__name__)

AUDIO_EFFECTS_DIR = "/data/UserData/UserLibrary/Audio Effects"
CORE_LIBRARY_DIR = "/data/CoreLibrary/Audio Effects"


class FxChainMacroHandler(BaseHandler):
    def handle_get(self):
        base_dir = AUDIO_EFFECTS_DIR
        if not os.path.exists(base_dir) and os.path.exists("examples/Audio Effects"):
            base_dir = "examples/Audio Effects"
        browser_html = generate_dir_html(
            base_dir,
            "",
            "/fx-chain",
            "preset_select",
            "select_preset",
            filter_key="fxchain",
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        return {
            "message": "Select an effect preset",
            "file_browser_html": browser_html,
            "selected_preset": None,
            "browser_root": base_dir,
            "parameters": [],
            "macro_values": {},
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        if action == "reset_preset":
            return self.handle_get()

        preset_path = form.getvalue("preset_select")
        if not preset_path:
            return self.format_error_response("No preset selected")

        if action == "select_preset":
            param_info = extract_effect_parameters(preset_path)
            if not param_info["success"]:
                return self.format_error_response(param_info["message"])
            base_dir = AUDIO_EFFECTS_DIR
            if not os.path.exists(base_dir) and os.path.exists("examples/Audio Effects"):
                base_dir = "examples/Audio Effects"
            browser_html = generate_dir_html(
                base_dir,
                "",
                "/fx-chain",
                "preset_select",
                "select_preset",
                filter_key="fxchain",
            )
            core_li = (
                '<li class="dir closed" data-path="Core Library">'
                '<span>📁 Core Library</span>'
                '<ul class="hidden"></ul></li>'
            )
            if browser_html.endswith('</ul>'):
                browser_html = browser_html[:-5] + core_li + '</ul>'

            is_core = preset_path.startswith(CORE_LIBRARY_DIR)
            if is_core:
                dest_name = os.path.basename(preset_path)
                if dest_name.endswith('.json'):
                    dest_name = dest_name[:-5] + '.ablpreset'
                save_path = os.path.join(AUDIO_EFFECTS_DIR, dest_name)
                message = f"Core Library preset will be saved to {save_path}"
            else:
                message = f"Editing {os.path.basename(preset_path)}"
            return {
                "message": message,
                "file_browser_html": browser_html,
                "selected_preset": preset_path,
                "browser_root": base_dir,
                "parameters": param_info.get("parameters", []),
                "macro_values": {},
            }

        if action == "save_mappings":
            mappings = {}
            names = {}
            for i in range(8):
                val = form.getvalue(f"macro_{i}_param")
                if val:
                    if "||" in val:
                        pname, ppath = val.split("||", 1)
                    else:
                        pname, ppath = val, None
                    mappings[i] = {"parameter": pname, "parameter_path": ppath}
                name = form.getvalue(f"macro_{i}_name")
                if name is not None:
                    names[i] = name
            new_name = form.getvalue("new_preset_name")
            if not new_name:
                new_name = os.path.basename(preset_path)
            if not new_name.endswith(".ablpreset"):
                new_name += ".ablpreset"
            dest_path = os.path.join(AUDIO_EFFECTS_DIR, new_name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            result = apply_macro_mappings(preset_path, mappings, dest_path, names)
            if not result["success"]:
                return self.format_error_response(result["message"])
            refresh_success, refresh_msg = refresh_library()
            message = result["message"]
            if refresh_success:
                message += " Library refreshed."
            else:
                message += f" Library refresh failed: {refresh_msg}"
            param_info = extract_effect_parameters(dest_path)
            return {
                "message": message,
                "file_browser_html": "",
                "selected_preset": dest_path,
                "browser_root": AUDIO_EFFECTS_DIR,
                "parameters": param_info.get("parameters", []),
                "macro_values": names,
            }

        return self.format_error_response("Unknown action")

