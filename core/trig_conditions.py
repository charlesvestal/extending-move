from typing import List, Dict, Tuple
import random
from math import gcd


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b) if a and b else 0


def apply_trig_conditions(
    notes: List[Dict[str, float]],
    loop_start: float,
    loop_end: float,
) -> Tuple[List[Dict[str, float]], float, bool]:
    """Expand notes according to trig conditions.

    Each note may contain a ``condition`` field. Ratio conditions like
    ``"1:4"`` extend the loop by the denominator and keep the note only
    on the specified iteration. Probability conditions such as ``"p50"``
    randomly keep notes on each iteration with the given percentage.

    The function returns the expanded note list, the new loop end and
    a flag indicating whether any condition was processed.
    """
    loop_len = loop_end - loop_start
    if loop_len <= 0:
        return notes, loop_end, False

    denominators = []
    found_cond = False
    for n in notes:
        cond = n.get("condition")
        if cond:
            found_cond = True
        if isinstance(cond, str) and ":" in cond:
            try:
                _, den = cond.split(":", 1)
                denominators.append(max(1, int(den)))
            except Exception:
                pass
    if not found_cond:
        return notes, loop_end, False
    cycle = 1
    for d in denominators:
        cycle = _lcm(cycle, d) if cycle else d
    cycle = max(cycle, 1)

    out: List[Dict[str, float]] = []
    for i in range(cycle):
        for n in notes:
            cond = n.get("condition")
            keep = True
            if isinstance(cond, str):
                if cond.startswith("p"):
                    try:
                        prob = int(cond[1:]) / 100.0
                    except Exception:
                        prob = 1.0
                    keep = random.random() < prob
                elif ":" in cond:
                    try:
                        num_s, den_s = cond.split(":", 1)
                        num = int(num_s)
                        den = int(den_s)
                        keep = (i % den) == (num - 1)
                    except Exception:
                        pass
            if not keep:
                continue
            new_note = {k: v for k, v in n.items() if k != "condition"}
            new_note["startTime"] = n.get("startTime", 0.0) + i * loop_len
            out.append(new_note)
    out.sort(key=lambda x: x.get("startTime", 0.0))
    new_end = loop_start + cycle * loop_len
    return out, new_end, True
