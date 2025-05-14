#!/usr/bin/env python3
import os
import json

def extract_macro_information(preset_path):
    """
    Extract macro information from a preset file.
    
    Args:
        preset_path: Path to the .ablpreset file
        
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
            - macros: List of dicts with macro info (index, name, mapped parameters)
    """
    try:
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        # Initialize macros dictionary
        macros = {}
        
        # Find all macros and their custom names
        def find_macros(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key.startswith("Macro") and key[5:].isdigit():
                        macro_index = int(key[5:])
                        
                        # Initialize macro if not exists
                        if macro_index not in macros:
                            macros[macro_index] = {
                                "index": macro_index,
                                "name": f"Macro {macro_index}",  # Default name
                                "parameters": []
                            }
                        
                        # Check if it has a custom name
                        if isinstance(value, dict) and "customName" in value:
                            macros[macro_index]["name"] = value["customName"]
                    
                    # Recursively search in nested dictionaries
                    new_path = f"{path}.{key}" if path else key
                    find_macros(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_macros(item, f"{path}[{i}]")
        
        # Find all parameters with macroMapping
        def find_macro_mappings(data, path=""):
            if isinstance(data, dict):
                # Check if this is a parameter with macroMapping
                if "macroMapping" in data and "macroIndex" in data["macroMapping"]:
                    macro_index = data["macroMapping"]["macroIndex"]
                    
                    # Get parameter name from path
                    param_name = path.split(".")[-1]
                    
                    # Initialize macro if not exists (shouldn't happen if find_macros is called first)
                    if macro_index not in macros:
                        macros[macro_index] = {
                            "index": macro_index,
                            "name": f"Macro {macro_index}",
                            "parameters": []
                        }
                    
                    # Add parameter info
                    param_info = {
                        "name": param_name,
                        "path": path
                    }
                    
                    # Add range if available
                    if "rangeMin" in data["macroMapping"] and "rangeMax" in data["macroMapping"]:
                        param_info["rangeMin"] = data["macroMapping"]["rangeMin"]
                        param_info["rangeMax"] = data["macroMapping"]["rangeMax"]
                    
                    macros[macro_index]["parameters"].append(param_info)
                
                # Recursively search in nested dictionaries
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    find_macro_mappings(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_macro_mappings(item, f"{path}[{i}]")
        
        # First find all macros
        find_macros(preset_data)
        
        # Then find all parameters with macroMapping
        find_macro_mappings(preset_data)
        
        # Convert dictionary to sorted list
        macros_list = [macros[i] for i in sorted(macros.keys())]
        
        return {
            'success': True,
            'message': f"Found {len(macros_list)} macros",
            'macros': macros_list
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error extracting macro information: {e}",
            'macros': []
        }

def update_preset_macro_names(preset_path, macro_updates):
    """
    Update the custom names of macros in a preset file.
    
    Args:
        preset_path: Path to the .ablpreset file
        macro_updates: Dictionary mapping macro indices to new custom names
        
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
    """
    try:
        # Load the preset file
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        # Find the device parameters where macros are defined
        def find_and_update_macros(data):
            updated_count = 0
            
            # Check if this is a device with parameters
            if isinstance(data, dict):
                # If this is a device with parameters that might contain macros
                if "parameters" in data and isinstance(data["parameters"], dict):
                    params = data["parameters"]
                    
                    # Look for Macro keys in parameters
                    for key in params.keys():
                        if key.startswith("Macro") and key[5:].isdigit():
                            macro_index = int(key[5:])
                            
                            # If we have an update for this macro
                            if macro_index in macro_updates:
                                # If it's already an object with customName
                                if isinstance(params[key], dict) and "value" in params[key]:
                                    params[key]["customName"] = macro_updates[macro_index]
                                    updated_count += 1
                                # If it's a direct value, convert to object with value and customName
                                else:
                                    original_value = params[key]
                                    params[key] = {
                                        "value": original_value,
                                        "customName": macro_updates[macro_index]
                                    }
                                    updated_count += 1
                
                # Recursively search in nested structures
                for key, value in data.items():
                    if isinstance(value, dict):
                        updated_count += find_and_update_macros(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                updated_count += find_and_update_macros(item)
            
            return updated_count
        
        # Update the macro names and get count of updates
        updated_count = find_and_update_macros(preset_data)
        
        # Write the updated preset back to the file
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {
            'success': True,
            'message': f"Updated {len(macro_updates)} macro names"
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error updating preset: {e}"
        }

def scan_for_drift_presets():
    """
    Scan the Move Track Presets directory for .ablpreset files containing drift devices.
    
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
            - presets: List of dicts with preset info (name and path)
    """
    try:
        presets_dir = "/data/UserData/UserLibrary/Track Presets"
        drift_presets = []

        # Check if directory exists
        if not os.path.exists(presets_dir):
            return {
                'success': False,
                'message': f"Track Presets directory not found: {presets_dir}",
                'presets': []
            }

        # Scan all .ablpreset files
        for filename in os.listdir(presets_dir):
            if filename.endswith('.ablpreset'):
                filepath = os.path.join(presets_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        preset_data = json.load(f)
                        
                    # Function to recursively search for drift devices
                    def has_drift_device(data):
                        if isinstance(data, dict):
                            if data.get('kind') == 'drift':
                                return True
                            return any(has_drift_device(v) for v in data.values())
                        elif isinstance(data, list):
                            return any(has_drift_device(item) for item in data)
                        return False

                    # If preset contains a drift device, add it to our list
                    if has_drift_device(preset_data):
                        preset_name = os.path.splitext(filename)[0]
                        drift_presets.append({
                            'name': preset_name,
                            'path': filepath
                        })

                except Exception as e:
                    print(f"Warning: Could not parse preset {filename}: {e}")
                    continue

        return {
            'success': True,
            'message': f"Found {len(drift_presets)} drift presets",
            'presets': drift_presets
        }

    except Exception as e:
        return {
            'success': False,
            'message': f"Error scanning presets: {e}",
            'presets': []
        }
