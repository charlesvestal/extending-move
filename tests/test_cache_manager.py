import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import cache_manager as cm


def test_set_get_invalidate():
    cm.set_cache("a", 1)
    assert cm.get_cache("a") == 1

    cm.invalidate_cache("a")
    assert cm.get_cache("a") is None

    cm.set_cache("b", 2)
    cm.invalidate_cache()
    assert cm.get_cache("b") is None
