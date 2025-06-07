#!/usr/bin/env python3
"""Handler for Drift editor interface with grouped parameters and images."""

import os
import json
import logging

from handlers.synth_param_editor_handler_class import SynthParamEditorHandler
from core.synth_preset_inspector_handler import load_drift_schema

logger = logging.getLogger(__name__)


class DriftEditorHandler(SynthParamEditorHandler):
    """Extended parameter editor that groups Drift parameters by section."""

    SECTION_MAP = [
        (
            "Oscillator Section",
            ["Oscillator1_", "Oscillator2_", "PitchModulation_"],
            "DriftOscSectionL12.png",
        ),
        (
            "Oscillator Mixer",
            ["Mixer_", "Filter_OscillatorThrough", "Filter_NoiseThrough"],
            "DriftOscMixL12.png",
        ),
        ("Filter Section", ["Filter_"], "DriftFilterL12.png"),
        (
            "Envelopes Section",
            ["Envelope1_", "Envelope2_", "CyclingEnvelope_"],
            "DriftEnvelopesL12.png",
        ),
        ("LFO Section", ["Lfo_"], "DriftLFOL12.png"),
        ("Mod Section", ["ModulationMatrix_"], "DriftModL12.png"),
        ("Global Section", ["Global_"], "DriftGlobalL12.png"),
    ]

    def generate_params_html(self, params):
        """Return HTML controls grouped by section."""
        if not params:
            return "<p>No parameters found.</p>"

        schema = load_drift_schema()
        html = ""
        index = 0
        used = set()

        def render_control(name, val):
            nonlocal index
            meta = schema.get(name, {})
            p_type = meta.get("type")
            ctrl = '<div class="param-item">'
            ctrl += f"<label>{name}: "
            if p_type == "enum" and meta.get("options"):
                ctrl += f'<select name="param_{index}_value">'
                for opt in meta["options"]:
                    selected = " selected" if str(val) == str(opt) else ""
                    ctrl += f'<option value="{opt}"{selected}>{opt}</option>'
                ctrl += "</select>"
            else:
                min_attr = (
                    f' min="{meta.get("min")}"' if meta.get("min") is not None else ""
                )
                max_attr = (
                    f' max="{meta.get("max")}"' if meta.get("max") is not None else ""
                )
                step_input = "any"
                if isinstance(val, (int, float)):
                    val_str = str(val)
                    if "." in val_str:
                        digits = len(val_str.split(".")[1].rstrip("0"))
                        step_input = str(10**-digits) if digits else "1"
                    else:
                        step_input = "1"
                step_slider = step_input
                rng_min = meta.get("min")
                rng_max = meta.get("max")
                if rng_min is not None and rng_max is not None:
                    if -1 <= rng_min and rng_max <= 1:
                        if step_slider == "any" or float(step_slider) > 0.01:
                            step_slider = "0.01"
                if step_input == "1" and step_slider != "any":
                    step_input = step_slider
                slider_step = (
                    f' step="{step_slider}"' if step_slider != "any" else ' step="any"'
                )
                input_step = (
                    f' step="{step_input}"' if step_input != "any" else ' step="any"'
                )
                ctrl += (
                    f'<input type="range" name="param_{index}_slider" value="{val}"{min_attr}{max_attr}{slider_step} '
                    f'oninput="this.nextElementSibling.value=this.value">'
                )
                ctrl += (
                    f'<input type="number" name="param_{index}_value" value="{val}"{min_attr}{max_attr}{input_step} '
                    f'oninput="this.previousElementSibling.value=this.value">'
                )
            ctrl += "</label>"
            ctrl += f'<input type="hidden" name="param_{index}_name" value="{name}">'
            ctrl += "</div>"
            index += 1
            return ctrl

        for title, prefixes, image in self.SECTION_MAP:
            section_params = [
                p for p in params if any(p["name"].startswith(pre) for pre in prefixes)
            ]
            if not section_params:
                continue
            for p in section_params:
                used.add(p["name"])
            html += f'<div class="drift-section"><h3>{title}</h3>'
            html += f'<img src="/static/drift_images/{image}" alt="{title}" class="drift-section-img">'
            html += '<div class="params-list">'
            for p in section_params:
                html += render_control(p["name"], p["value"])
            html += "</div></div>"

        leftover = [p for p in params if p["name"] not in used]
        if leftover:
            html += '<div class="drift-section"><h3>Other Parameters</h3><div class="params-list">'
            for p in leftover:
                html += render_control(p["name"], p["value"])
            html += "</div></div>"

        return html
