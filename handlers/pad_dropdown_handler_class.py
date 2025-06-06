from handlers.base_handler import BaseHandler

class PadDropdownHandler(BaseHandler):
    """Provide data for the pad dropdown demo page."""

    def handle_get(self):
        pads = list(range(1, 33))
        return {"pad_numbers": pads}
