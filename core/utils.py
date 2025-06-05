import json
from typing import Any, Dict


def load_set_template(template_path: str) -> Dict[str, Any]:
    """Load a set template from ``template_path`` and return the parsed data."""
    try:
        with open(template_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load template: {str(e)}")

