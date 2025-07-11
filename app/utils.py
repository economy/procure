import json
from pathlib import Path

def load_factor_templates() -> dict[str, list[str]]:
    """Loads the comparison factor templates from the JSON file."""
    templates_path = Path(__file__).parent / "factor_templates.json"
    with open(templates_path, "r") as f:
        return json.load(f) 