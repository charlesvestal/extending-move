import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(__name__ + "_orig", Path(__file__).with_name("move-webserver.py"))
module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(module)
sys.modules[__name__] = module

