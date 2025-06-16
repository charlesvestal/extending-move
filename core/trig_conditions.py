from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math


def _loops_for(cond: str) -> int:
    if not cond:
        return 1
    if ':' in cond:
        try:
            _, b = cond.split(':', 1)
            return max(1, int(b))
        except Exception:
            return 1
    if cond.startswith('p'):
        try:
            val = int(cond[1:])
            if val > 0:
                return max(1, round(100 / val))
        except Exception:
            pass
    return 1


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // math.gcd(a, b)


def apply_trig_conditions(
    notes: List[Dict[str, Any]],
    loop_start: float,
    loop_end: float,
    region_end: float,
) -> Tuple[List[Dict[str, Any]], float, float]:
    """Expand notes with Elektron-style trig conditions."""
    length = loop_end - loop_start
    loops = 1
    for n in notes:
        loops = _lcm(loops, _loops_for(str(n.get('cond') or '')))
    if loops == 1:
        return notes, region_end, loop_end

    new_notes: List[Dict[str, Any]] = []
    for i in range(loops):
        shift = i * length
        for n in notes:
            cond = n.get('cond')
            include = True
            if cond:
                if ':' in cond:
                    try:
                        a_s, b_s = cond.split(':', 1)
                        a = int(a_s)
                        b = int(b_s)
                        include = (i % b) == (a - 1)
                    except Exception:
                        include = True
                elif cond.startswith('p'):
                    try:
                        val = int(cond[1:])
                        mod = max(1, round(100 / val))
                        include = (i % mod) == 0
                    except Exception:
                        include = True
            if include:
                new_n = {k: v for k, v in n.items() if k != 'cond'}
                new_n['startTime'] = float(n.get('startTime', 0.0)) + shift
                new_notes.append(new_n)
    new_notes.sort(key=lambda x: x.get('startTime', 0.0))
    final_len = length * loops
    new_region = max(region_end, loop_start + final_len)
    new_loop_end = max(loop_end, loop_start + final_len)
    return new_notes, new_region, new_loop_end
