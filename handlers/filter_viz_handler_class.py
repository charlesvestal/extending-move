#!/usr/bin/env python3
from handlers.base_handler import BaseHandler
from core.filter_visualizer import compute_chain_response


class FilterVizHandler(BaseHandler):
    """Handle requests for the filter visualization feature."""

    def handle_get(self):
        return {
            "message": "Adjust parameters to visualize the filter response",
            "message_type": "info",
        }

    def handle_post(self, form):
        f1_type = form.getvalue("filter1_type", "Lowpass")
        f1_freq = float(form.getvalue("filter1_freq", 1000))
        f1_res = float(form.getvalue("filter1_res", 0.0))
        f1_slope = form.getvalue("filter1_slope", "12")
        f1_morph = float(form.getvalue("filter1_morph", 0.0))

        filter1 = {
            "filter_type": f1_type,
            "cutoff": f1_freq,
            "resonance": f1_res,
            "slope": f1_slope,
            "morph": f1_morph,
        }

        if form.getvalue("use_filter2"):
            f2_type = form.getvalue("filter2_type", "Lowpass")
            f2_freq = float(form.getvalue("filter2_freq", 1000))
            f2_res = float(form.getvalue("filter2_res", 0.0))
            f2_slope = form.getvalue("filter2_slope", "12")
            f2_morph = float(form.getvalue("filter2_morph", 0.0))
            filter2 = {
                "filter_type": f2_type,
                "cutoff": f2_freq,
                "resonance": f2_res,
                "slope": f2_slope,
                "morph": f2_morph,
            }
        else:
            filter2 = None

        routing = form.getvalue("routing", "Serial")
        result = compute_chain_response(filter1, filter2, routing)
        if len(result) == 2:
            freq, mag = result
            data = {"freq": freq, "mag": mag}
        else:
            freq, mag1, mag2 = result
            data = {"freq": freq, "mag1": mag1, "mag2": mag2}

        return self.format_json_response(data)
