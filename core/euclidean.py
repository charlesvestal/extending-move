from typing import List, Dict, Any


def euclidean_rhythm(steps: int, pulses: int, rotate: int = 0) -> List[int]:
    """Generate a Euclidean rhythm as step indices (0-based)."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    pulses = max(0, min(pulses, steps))
    rotate = rotate % steps
    pattern: List[int] = []
    bucket = 0
    for step in range(steps):
        bucket += pulses
        if bucket >= steps:
            bucket -= steps
            pattern.append((step + rotate) % steps)
    return sorted(pattern)


def apply_euclidean_fill(
    notes: List[Dict[str, Any]],
    note_number: int,
    loop_start: float,
    loop_end: float,
    steps: int,
    pulses: int,
    rotate: int,
    grid: float,
    repeat: bool = False,
) -> List[Dict[str, Any]]:
    """Return new notes list with Euclidean pattern applied to the given row.

    If ``repeat`` is True, the generated pattern is repeated until ``loop_end``.
    """
    onsets = euclidean_rhythm(steps, pulses, rotate)
    new_notes = [
        n
        for n in notes
        if not (
            n.get("noteNumber") == note_number
            and loop_start <= n.get("startTime", 0) < loop_end
        )
    ]
    pattern_len = steps * grid
    base = 0.0
    while True:
        for step in onsets:
            start = loop_start + base + step * grid
            if start >= loop_end:
                break
            new_notes.append(
                {
                    "noteNumber": note_number,
                    "startTime": start,
                    "duration": grid,
                    "velocity": 100,
                    "offVelocity": 0,
                }
            )
        if not repeat or loop_start + base + pattern_len >= loop_end:
            break
        base += pattern_len
    new_notes.sort(key=lambda x: x["startTime"])
    return new_notes

