#!/usr/bin/env python3
import os
import json
from handlers.base_handler import BaseHandler
from core.audio_effect_rack_handler import (
    list_available_devices,
    extract_effect_parameters,
    create_effect_rack,
    DEFAULT_OUTPUT_DIR,
)
from core.refresh_handler import refresh_library


class AudioEffectRackHandler(BaseHandler):
    def _prepare_options(self):
        devices = list_available_devices()
        options = []
        params_map = {}
        for d in devices:
            options.append({"kind": d, "name": d})
            params_map[d] = extract_effect_parameters(d)
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
        device_kinds = []
        macro_map = {}
        for i in range(4):
            kind = form.getvalue(f"effect_{i}")
            if kind:
                device_kinds.append(kind)
                param = form.getvalue(f"macro_{i}_param")
                if param:
                    macro_map[i] = {"device_index": len(device_kinds) - 1, "parameter": param}
        if not device_kinds:
            return self.format_error_response("No effects selected")
        filename = preset_name
        if not filename.endswith(".ablpreset") and not filename.endswith(".json"):
            filename += ".ablpreset"
        out_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
        result = create_effect_rack(device_kinds, macro_map, out_path, preset_name)
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
