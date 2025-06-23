#!/usr/bin/env python3
"""Web handler for the FX Chain editor."""

import json
from handlers.base_handler import BaseHandler
from core.fx_chain_handler import (
    load_fx_presets,
    create_fx_chain,
)


class FxChainHandler(BaseHandler):
    def handle_get(self):
        presets = load_fx_presets()
        return {
            "effects": list(presets.keys()),
            "presets_json": json.dumps(presets),
            "message": "Select effects, presets and map parameters",
            "message_type": "info",
        }

    def handle_post(self, form):
        effect_presets = [form.getvalue(f"effect{i}_preset") for i in range(1, 5)]
        preset_name = form.getvalue("preset_name")
        if not preset_name:
            return self.format_error_response("Preset name required")

        knob_map = {}
        for i in range(8):
            eff_idx = form.getvalue(f"knob{i}_effect")
            param = form.getvalue(f"knob{i}_param")
            if eff_idx and param:
                try:
                    eff_idx = int(eff_idx) - 1
                except ValueError:
                    continue
                knob_map[i] = {"effect_index": eff_idx, "parameter": param}

        param_values = {}
        for idx in range(4):
            vals = {}
            prefix = f"effect{idx + 1}_param_"
            for key, val in form.items():
                if key.startswith(prefix):
                    param = key[len(prefix) :]
                    vals[param] = val
            if vals:
                param_values[idx] = vals

        result = create_fx_chain(effect_presets, knob_map, preset_name, param_values)
        msg_type = "success" if result.get("success") else "error"
        presets = load_fx_presets()
        return {
            "effects": list(presets.keys()),
            "presets_json": json.dumps(presets),
            "message": result.get("message"),
            "message_type": msg_type,
        }
