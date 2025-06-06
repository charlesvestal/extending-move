from handlers.base_handler import BaseHandler
from core.pad_colors import PAD_COLORS, PAD_COLOR_LABELS

class ColorDropdownHandler(BaseHandler):
    """Provide data for the color dropdown demo page."""

    def handle_get(self):
        colors = [PAD_COLORS[i] for i in sorted(PAD_COLORS)]
        names = [PAD_COLOR_LABELS[i] for i in sorted(PAD_COLOR_LABELS)]
        return {"pad_colors": colors, "pad_names": names}

