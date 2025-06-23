#!/usr/bin/env python3
"""Web handler for the FX Chain editor."""

import json
from handlers.base_handler import BaseHandler
from core.fx_chain_handler import (
    DEFAULT_EFFECT_PRESETS,
    get_effect_parameters,
    create_fx_chain,
)


class FxChainHandler(BaseHandler):
    def handle_get(self):
        effect_params = {
            k: get_effect_parameters(k) for k in DEFAULT_EFFECT_PRESETS.keys()
        }
        return {
            "effects": list(DEFAULT_EFFECT_PRESETS.keys()),
            "effect_params_json": json.dumps(effect_params),
            "message": "Select effects and map parameters to macros",
            "message_type": "info",
        }

    def handle_post(self, form):
        effect_kinds = [form.getvalue(f"effect{i}") for i in range(1, 5)]
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

        result = create_fx_chain(effect_kinds, knob_map, preset_name)
        msg_type = "success" if result.get("success") else "error"
        effect_params = {
            k: get_effect_parameters(k) for k in DEFAULT_EFFECT_PRESETS.keys()
        }
        return {
            "effects": list(DEFAULT_EFFECT_PRESETS.keys()),
            "effect_params_json": json.dumps(effect_params),
            "message": result.get("message"),
            "message_type": msg_type,
        }
