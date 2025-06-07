PAD_COLORS = {
    1: (255, 25, 23),
    2: (255, 142, 12),
    3: (255, 98, 41),
    4: (255, 186, 115),
    5: (215, 74, 9),
    6: (231, 231, 127),
    7: (255, 233, 94),
    8: (192, 255, 112),
    9: (135, 255, 109),
    10: (93, 219, 32),
    11: (161, 206, 47),
    12: (106, 237, 196),
    13: (0, 206, 197),
    14: (0, 212, 198),
    15: (29, 247, 243),
    16: (113, 167, 231),
    17: (34, 133, 240),
    18: (125, 87, 229),
    19: (34, 171, 240),
    20: (150, 139, 233),
    21: (178, 139, 233),
    22: (223, 139, 233),
    23: (199, 90, 214),
    24: (247, 35, 141),
    25: (227, 95, 200),
}

# Human-readable names for each pad color
PAD_COLOR_LABELS = {
    1: "Scarlet Red",
    2: "Pumpkin Orange",
    3: "Tangerine Blaze",
    4: "Salmon Glow",
    5: "Rust",
    6: "Khaki Tan",
    7: "Sunny Yellow",
    8: "Pale Green",
    9: "Fresh Green",
    10: "Lime",
    11: "Olive",
    12: "Aqua",
    13: "Turquoise",
    14: "Bright Turquoise",
    15: "Aqua Splash",
    16: "Sky Blue",
    17: "Azure",
    18: "Electric Purple",
    19: "Bright Cyan",
    20: "Lavender",
    21: "Lilac",
    22: "Soft Lavender",
    23: "Orchid",
    24: "Hot Pink",
    25: "Fuchsia",
}

def rgb_string(color_id):
    rgb = PAD_COLORS.get(color_id)
    if rgb:
        return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
    return ""