PAD_COLORS = {
    1: (255, 25, 23),
    2: (255, 142, 12),
    3: (255, 68, 0),
    4: (255, 186, 115),
    5: (248, 98, 28),
    6: (193, 193, 144),
    7: (255, 233, 94),
    8: (192, 255, 112),
    9: (135, 255, 109),
    10: (93, 219, 32),
    11: (161, 206, 47),
    12: (96, 242, 200),
    13: (0, 206, 197),
    14: (0, 212, 198),
    15: (0, 157, 192),
    16: (22, 124, 194),
    17: (0, 106, 190),
    18: (71, 73, 135),
    19: (0, 118, 186),
    20: (64, 92, 140),
    21: (75, 81, 129),
    22: (130, 82, 200),
    23: (156, 83, 183),
    24: (220, 16, 87),
    25: (217, 43, 255),
}

# CSS-style names for each pad color based on nearest match
PAD_COLOR_NAMES = {
    1: "red",
    2: "darkorange",
    3: "orangered",
    4: "lightsalmon",
    5: "chocolate",
    6: "tan",
    7: "khaki",
    8: "palegreen",
    9: "lightgreen",
    10: "limegreen",
    11: "yellowgreen",
    12: "aquamarine",
    13: "darkturquoise",
    14: "darkturquoise",
    15: "lightseagreen",
    16: "steelblue",
    17: "darkcyan",
    18: "darkslateblue",
    19: "darkcyan",
    20: "darkslateblue",
    21: "darkslateblue",
    22: "slateblue",
    23: "darkorchid",
    24: "crimson",
    25: "fuchsia",
}

def rgb_string(color_id):
    rgb = PAD_COLORS.get(color_id)
    if rgb:
        return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
    return ""

def color_name(color_id):
    """Return a CSS-style color name for the given pad color ID."""
    return PAD_COLOR_NAMES.get(color_id, "")
