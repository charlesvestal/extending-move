"""Overview handler: pad grid, set metadata (BPM/key/Camelot), disk and system stats.

Reads the local filesystem directly — no SSH needed since this runs on Move.
Uses os.getxattr() for xattr reads (Python stdlib on Linux, no subprocess).
"""
import json
import os
import shutil
from pathlib import Path
from typing import Optional

from core.config import MSETS_DIRECTORY
from core.pad_colors import PAD_COLORS, move_color_to_ui

SETTINGS_FILE = '/data/UserData/settings/Settings.json'
SETS_ROOT = MSETS_DIRECTORY


def _read_xattr(path: str, attr_name: str) -> Optional[str]:
    """Read a single xattr via os.getxattr() — no subprocess required."""
    try:
        raw = os.getxattr(path, attr_name)
        return raw.decode('utf-8', errors='replace').strip() or None
    except Exception:
        return None


_ROOT_NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

def _parse_song_abl(set_path: str) -> dict:
    """Parse Song.abl (raw JSON) for BPM, key, and scale. Returns {} on failure."""
    try:
        abl_path = os.path.join(set_path, 'Song.abl')
        with open(abl_path, 'r') as f:
            data = json.load(f)
        tempo = data.get('tempo')
        bpm = round(float(tempo), 1) if tempo else None
        root = data.get('rootNote')
        key = _ROOT_NOTE_NAMES[int(root) % 12] if root is not None else None
        scale_raw = data.get('scale', '')
        scale = 'minor' if 'minor' in scale_raw.lower() else 'major' if scale_raw else None
        return {'bpm': bpm, 'key': key, 'scale': scale}
    except Exception:
        return {}


def _key_to_camelot(key: str, scale: str) -> Optional[str]:
    """Map a key + scale to a Camelot wheel code."""
    TABLE = {
        ('C', 'major'): '8B',  ('A', 'minor'): '8A',
        ('G', 'major'): '9B',  ('E', 'minor'): '9A',
        ('D', 'major'): '10B', ('B', 'minor'): '10A',
        ('A', 'major'): '11B', ('F#', 'minor'): '11A',
        ('E', 'major'): '12B', ('C#', 'minor'): '12A',
        ('B', 'major'): '1B',  ('G#', 'minor'): '1A',
        ('F#', 'major'): '2B', ('D#', 'minor'): '2A',
        ('Db', 'major'): '3B', ('Bb', 'minor'): '3A',
        ('Ab', 'major'): '4B', ('F', 'minor'): '4A',
        ('Eb', 'major'): '5B', ('C', 'minor'): '5A',
        ('Bb', 'major'): '6B', ('G', 'minor'): '6A',
        ('F', 'major'): '7B',  ('D', 'minor'): '7A',
    }
    if not key or not scale:
        return None
    return TABLE.get((key, scale.lower()))


def get_sets_data() -> dict:
    """Return full set metadata: pad grid, BPM, key, Camelot, disk usage, active slot."""
    sets_data = []
    try:
        sets_root = Path(SETS_ROOT)
        for uuid_dir in sorted(sets_root.iterdir()):
            if not uuid_dir.is_dir():
                continue
            children = [d for d in uuid_dir.iterdir() if d.is_dir()]
            if not children:
                continue
            set_dir = children[0]
            uuid_path = str(uuid_dir)

            slot_val  = _read_xattr(uuid_path, 'user.song-index')
            color_val = _read_xattr(uuid_path, 'user.song-color')
            try:
                slot = int(slot_val) if slot_val is not None else None
            except (ValueError, TypeError):
                slot = None
            try:
                xattr_color = int(color_val) if color_val is not None else None
            except (ValueError, TypeError):
                xattr_color = None

            parsed = _parse_song_abl(str(set_dir))
            bpm   = parsed.get('bpm')
            key   = parsed.get('key')
            scale = parsed.get('scale')
            camelot = _key_to_camelot(key, scale) if key and scale else None

            color_id = move_color_to_ui(xattr_color)
            rgb = PAD_COLORS.get(color_id)
            color_css = f'rgb({rgb[0]},{rgb[1]},{rgb[2]})' if rgb else None

            sets_data.append({
                'name':        set_dir.name,
                'path':        str(set_dir),
                'uuid':        uuid_dir.name,
                'modified':    uuid_dir.stat().st_mtime,
                'bpm':         bpm,
                'key':         key,
                'mode':        scale,
                'camelot':     camelot,
                'slot':        slot,
                'xattr_color': xattr_color,
                'color_id':    color_id,
                'color_css':   color_css,
            })
    except Exception:
        pass

    sets_data.sort(key=lambda s: s['slot'] if s['slot'] is not None else 9999)

    disk = None
    try:
        usage = shutil.disk_usage('/data/UserData')
        disk = {
            'total_gb':     round(usage.total / 1024 ** 3, 1),
            'used_gb':      round(usage.used  / 1024 ** 3, 1),
            'free_gb':      round(usage.free  / 1024 ** 3, 1),
            'percent_used': round(usage.used / usage.total * 100),
        }
    except Exception:
        pass

    current_slot = get_active_slot()

    return {
        'sets':         sets_data,
        'disk':         disk,
        'total_sets':   len(sets_data),
        'current_slot': current_slot,
    }


def get_active_slot() -> Optional[int]:
    """Read currentSongIndex from Settings.json."""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
        val = data.get('currentSongIndex')
        return int(val) if val is not None else None
    except Exception:
        return None


def get_system_stats() -> dict:
    """Read CPU load averages and memory usage from /proc."""
    stats = {}
    try:
        parts = open('/proc/loadavg').read().split()
        stats['load_1']  = float(parts[0])
        stats['load_5']  = float(parts[1])
        stats['load_15'] = float(parts[2])
    except Exception:
        pass
    try:
        meminfo = {}
        for line in open('/proc/meminfo'):
            k, v = line.split(':', 1)
            meminfo[k.strip()] = int(v.strip().split()[0])
        total_kb = meminfo.get('MemTotal', 0)
        avail_kb = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
        used_kb  = total_kb - avail_kb
        stats['mem_total_mb'] = round(total_kb / 1024)
        stats['mem_used_mb']  = round(used_kb  / 1024)
        stats['mem_pct']      = round(used_kb / total_kb * 100) if total_kb else 0
    except Exception:
        pass
    try:
        stats['cpu_count'] = os.cpu_count() or 1
    except Exception:
        pass
    return stats
