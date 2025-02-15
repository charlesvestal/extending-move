from pathlib import Path
import json
import logging
from handlers.base_handler import BaseHandler

# Simple print-based debugging
def debug(msg):
    print(f"[DEBUG] {msg}")

def warning(msg):
    print(f"[WARNING] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")

class SynthPresetInspectorHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        
    def toggle_polyphony(self, preset_path):
        """Toggle the polyphony value between Mono and Poly for a preset."""
        try:
            with open(preset_path) as f:
                data = json.load(f)

            def find_and_update_device(data):
                if "chains" in data:
                    for chain in data["chains"]:
                        if "devices" in chain:
                            for device in chain["devices"]:
                                kind = device.get("kind", "").lower()
                                if kind in {"wavetable", "drift"}:
                                    params = device.get("parameters", {})
                                    if kind == "wavetable":
                                        current = params.get("MonoPoly", "Mono")
                                        params["MonoPoly"] = "Poly" if current == "Mono" else "Mono"
                                    else:  # drift
                                        current = params.get("Global_VoiceMode", "Mono")
                                        params["Global_VoiceMode"] = "Poly" if current == "Mono" else "Mono"
                                    return device
                                elif kind == "instrumentrack":
                                    result = find_and_update_device(device)
                                    if result:
                                        return result
                return None

            device = find_and_update_device(data)
            if device:
                with open(preset_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                device_kind = device.get("kind", "").lower()
                polyphony = device.get("parameters", {}).get(
                    "MonoPoly" if device_kind == "wavetable" 
                    else "Global_VoiceMode",
                    "Unknown"
                )
                return {"polyphony": polyphony}
            
            return {"error": "No wavetable or drift device found"}
        except Exception as e:
            error(f"Error toggling polyphony: {str(e)}")
            return {"error": str(e)}

    def handle(self):
        presets = []
        preset_dir = Path("examples/Track Presets")  # Update path for server deployment
        debug(f"Looking for presets in: {preset_dir.absolute()}")
        debug(f"Found these files: {list(preset_dir.glob('**/*.ablpreset'))}")
        
        for preset_path in preset_dir.glob("**/*.ablpreset"):
            with open(preset_path) as f:
                try:
                    data = json.load(f)
                    debug(f"Processing preset: {preset_path}")
                    
                    # Look for wavetable/drift devices in nested structure
                    def find_device(data):
                        if "chains" in data:
                            for chain in data["chains"]:
                                if "devices" in chain:
                                    for device in chain["devices"]:
                                        kind = device.get("kind", "").lower()
                                        if kind in {"wavetable", "drift"}:
                                            return device
                                        # Recurse into nested instrument racks
                                        if kind == "instrumentrack":
                                            nested_device = find_device(device)
                                            if nested_device:
                                                return nested_device
                        return None
                    
                    device = find_device(data)
                    if device:
                        device_kind = device.get("kind", "").lower()
                        polyphony = device.get("parameters", {}).get(
                            "MonoPoly" if device_kind == "wavetable" 
                            else "Global_VoiceMode",
                            "Unknown"
                        )
                        debug(f"Found {device_kind} device with polyphony: {polyphony}")
                        debug(f"Found polyphony: {polyphony} for {preset_path}")
                        presets.append({
                            "name": preset_path.stem,
                            "path": str(preset_path),
                            "polyphony": polyphony
                        })
                    else:
                        debug(f"Skipping {preset_path} - device kind {device_kind} not wavetable or drift")
                except json.JSONDecodeError as e:
                    error(f"Error parsing JSON in {preset_path}: {str(e)}")
                    continue
                except Exception as e:
                    error(f"Unexpected error processing {preset_path}: {str(e)}")
                    continue
        
        options_html = []
        for preset in presets:
            options_html.append(f'<option value="{preset["path"]}">{preset["name"]}</option>')
        
        initial_polyphony = presets[0]["polyphony"] if presets else "Unknown"
        polyphony_html = f'<p>Polyphony: {initial_polyphony}</p>'
        
        return {
            "options": "\n".join(options_html),
            "polyphony_html": polyphony_html
        }
