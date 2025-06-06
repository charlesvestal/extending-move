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

# Names are approximate interpretations of the RGB values.
PAD_COLOR_NAMES = {
    1: "Red",
    2: "Orange",
    3: "Bright Orange",
    4: "Peach",
    5: "Burnt Orange",
    6: "Beige",
    7: "Yellow",
    8: "Lime",
    9: "Light Green",
    10: "Green",
    11: "Olive",
    12: "Aqua",
    13: "Teal",
    14: "Turquoise",
    15: "Cyan",
    16: "Sky Blue",
    17: "Ocean Blue",
    18: "Indigo",
    19: "Azure",
    20: "Slate Blue",
    21: "Steel Blue",
    22: "Violet",
    23: "Magenta",
    24: "Pink",
    25: "Purple",
}

def rgb_string(color_id: int) -> str:
    rgb = PAD_COLORS.get(color_id)
    if rgb:
        return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
    return ""

def color_name(color_id: int) -> str:
    return PAD_COLOR_NAMES.get(color_id, str(color_id))
