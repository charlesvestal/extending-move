#!/usr/bin/env python3
import os
import json
from handlers.base_handler import BaseHandler
from core.audio_effect_rack_handler import (
    list_audio_effect_presets,
    extract_effect_parameters,
    create_effect_rack,
    DEFAULT_OUTPUT_DIR,
)
from core.refresh_handler import refresh_library


class AudioEffectRackHandler(BaseHandler):
    def _prepare_options(self):
        presets = list_audio_effect_presets()
        options = []
        params_map = {}
        for p in presets:
            name = os.path.splitext(os.path.basename(p))[0]
            options.append({"path": p, "name": name})
            params_map[p] = extract_effect_parameters(p)
        return options, params_map

    def handle_get(self):
        opts, params = self._prepare_options()
        return {
            "message": "Select effects and assign macros",
            "message_type": "info",
            "effects": opts,
            "params_json": json.dumps(params),
        }

    def handle_post(self, form):
        valid, err = self.validate_action(form, "save_rack")
        if not valid:
            return err
        preset_name = form.getvalue("preset_name") or "New Rack"
        effect_paths = []
        macro_map = {}
        for i in range(4):
            path = form.getvalue(f"effect_{i}")
            if path:
                effect_paths.append(path)
                param = form.getvalue(f"macro_{i}_param")
                if param:
                    macro_map[i] = {"device_index": len(effect_paths) - 1, "parameter": param}
        if not effect_paths:
            return self.format_error_response("No effects selected")
        filename = preset_name
        if not filename.endswith(".ablpreset") and not filename.endswith(".json"):
            filename += ".ablpreset"
        out_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
        result = create_effect_rack(effect_paths, macro_map, out_path, preset_name)
        if not result.get("success"):
            return self.format_error_response(result.get("message", "Failed"))
        refresh_success, refresh_message = refresh_library()
        msg = result["message"]
        if refresh_success:
            msg += " Library refreshed."
        else:
            msg += f" Library refresh failed: {refresh_message}"
        opts, params = self._prepare_options()
        return {
            "message": msg,
            "message_type": "success",
            "effects": opts,
            "params_json": json.dumps(params),
        }
