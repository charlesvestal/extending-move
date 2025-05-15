#!/usr/bin/env python3
import os
import json

def extract_available_parameters(preset_path):
    """
    Extract available parameters from drift devices in a preset file.
    
    Args:
        preset_path: Path to the .ablpreset file
        
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
            - parameters: List of parameter names
    """
    try:
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        # Set to store unique parameter names
        parameters = set()
        
        # Dictionary to store parameter paths
        parameter_paths = {}
        
        # Dictionary to store drift device paths
        drift_device_paths = set()
        
        # First, find all drift devices
        def find_drift_devices(data, path=""):
            if isinstance(data, dict):
                # Check if this is a drift device
                if data.get('kind') == 'drift':
                    drift_device_paths.add(path)
                    print(f"Found drift device at path: {path}")
                
                # Recursively search in nested dictionaries
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    find_drift_devices(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_drift_devices(item, f"{path}[{i}]")
        
        # Find all drift devices
        find_drift_devices(preset_data)
        
        # Function to recursively find parameters in drift devices
        def find_parameters(data, path=""):
            if isinstance(data, dict):
                # If this is a parameters object
                if path.endswith("parameters"):
                    # Check if this parameters object belongs to a drift device
                    is_drift_parameter = False
                    for drift_path in drift_device_paths:
                        if path.startswith(drift_path) or drift_path.startswith(path.rsplit('.parameters', 1)[0]):
                            is_drift_parameter = True
                            break
                    
                    if is_drift_parameter:
                        # Add all keys that aren't "Enabled" or start with "Macro"
                        for key in data.keys():
                            if key != "Enabled" and not key.startswith("Macro"):
                                parameters.add(key)
                                parameter_paths[key] = f"{path}.{key}"
                                print(f"Adding drift parameter: {key} at path: {path}.{key}")
                
                # Recursively search in nested dictionaries
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    find_parameters(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_parameters(item, f"{path}[{i}]")
        
        # Find all parameters
        find_parameters(preset_data)
        
        # Convert set to sorted list
        parameters_list = sorted(list(parameters))
        
        return {
            'success': True,
            'message': f"Found {len(parameters_list)} parameters",
            'parameters': parameters_list,
            'parameter_paths': parameter_paths
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error extracting parameters: {e}",
            'parameters': []
        }

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
            - mapped_parameters: Dict mapping parameter names to their macro indices
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
        
        # Dictionary to track which parameters are already mapped to macros
        mapped_parameters = {}
        
        # Find all parameters with macroMapping
        def find_macro_mappings(data, path=""):
            if isinstance(data, dict):
                # Check if this is a parameter with macroMapping
                if "macroMapping" in data and "macroIndex" in data["macroMapping"]:
                    macro_index = data["macroMapping"]["macroIndex"]
                    
                    # Get parameter name from path
                    param_name = path.split(".")[-1]
                    
                    # Track this parameter as mapped
                    mapped_parameters[param_name] = {
                        "macro_index": macro_index,
                        "path": path
                    }
                    
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
            'macros': macros_list,
            'mapped_parameters': mapped_parameters
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

def update_preset_parameter_mappings(preset_path, parameter_updates):
    """
    Update parameter mappings and range values for macros in a preset file.
    If a parameter is already mapped to a different macro, the old mapping will be removed.
    
    Args:
        preset_path: Path to the .ablpreset file
        parameter_updates: Dictionary mapping macro indices to parameter update info
            {
                macro_index: {
                    'parameter': 'Parameter_Name',
                    'parameter_path': 'Full.Path.To.Parameter',  # Optional
                    'rangeMin': value,  # Optional
                    'rangeMax': value   # Optional
                }
            }
    
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
    """
    try:
        # Load the preset file
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        # Track parameters that were updated
        updated_params = []
        
        # Debug: Print parameter updates
        print(f"Parameter updates: {parameter_updates}")
        
        # Helper function to get the object at a specific path
        def get_object_at_path(data, path):
            """Get the object at the specified path."""
            if not path:
                return data
            
            parts = path.split(".")
            current = data
            
            for part in parts:
                # Handle array indices
                if "[" in part and part.endswith("]"):
                    name, index_str = part.split("[", 1)
                    index = int(index_str[:-1])  # Remove the closing bracket
                    
                    if name:
                        if name not in current:
                            return None
                        current = current[name]
                    
                    if not isinstance(current, list) or index >= len(current):
                        return None
                    current = current[index]
                else:
                    if part not in current:
                        return None
                    current = current[part]
            
            return current
        
        # First, get information about currently mapped parameters
        macro_info = extract_macro_information(preset_path)
        mapped_parameters = {}
        if macro_info['success']:
            mapped_parameters = macro_info.get('mapped_parameters', {})
        
        # Function to remove existing macro mappings for a parameter
        def remove_existing_mapping(param_name):
            if param_name in mapped_parameters:
                mapping_info = mapped_parameters[param_name]
                param_path = mapping_info['path']
                parent_path = param_path.rsplit(".", 1)[0]
                key = param_path.split(".")[-1]
                
                parent = get_object_at_path(preset_data, parent_path)
                if parent and key in parent and isinstance(parent[key], dict) and "macroMapping" in parent[key]:
                    print(f"Removing existing mapping for {param_name} from macro {mapping_info['macro_index']}")
                    # Remove the macroMapping
                    del parent[key]["macroMapping"]
                    return True
            return False
        
        # First, try to update parameters using direct paths
        for macro_index, update_info in parameter_updates.items():
            if update_info.get('parameter_path'):
                param_path = update_info['parameter_path']
                param_name = param_path.split(".")[-1]
                parent_path = param_path.rsplit(".", 1)[0]
                
                print(f"Using direct path for parameter {param_name}: {param_path}")
                print(f"Parent path: {parent_path}")
                
                # Remove existing mapping if parameter is already mapped to a different macro
                if param_name in mapped_parameters and mapped_parameters[param_name]['macro_index'] != macro_index:
                    remove_existing_mapping(param_name)
                
                parent = get_object_at_path(preset_data, parent_path)
                key = param_path.split(".")[-1]
                
                if parent and key in parent:
                    print(f"Found parameter using direct path: {param_name}")
                    print(f"Parameter value: {parent[key]}, Type: {type(parent[key])}")
                    
                    # If this is a simple value (not an object with a value property)
                    if not isinstance(parent[key], dict) or "value" not in parent[key]:
                        # Store the original value
                        original_value = parent[key]
                        
                        # Replace with an object that has value and macroMapping
                        parent[key] = {
                            "value": original_value,
                            "macroMapping": {
                                "macroIndex": macro_index
                            }
                        }
                    else:
                        # It's already an object with a value property
                        # Create macroMapping if it doesn't exist
                        if "macroMapping" not in parent[key]:
                            parent[key]["macroMapping"] = {}
                        
                        # Set the macro index
                        parent[key]["macroMapping"]["macroIndex"] = macro_index
                    
                    # Add range values if provided
                    if update_info.get('rangeMin') is not None and update_info.get('rangeMin') != "":
                        parent[key]["macroMapping"]["rangeMin"] = float(update_info['rangeMin'])
                    elif "macroMapping" in parent[key] and "rangeMin" in parent[key]["macroMapping"]:
                        # Remove rangeMin if it exists and the update value is empty
                        del parent[key]["macroMapping"]["rangeMin"]
                        
                    if update_info.get('rangeMax') is not None and update_info.get('rangeMax') != "":
                        parent[key]["macroMapping"]["rangeMax"] = float(update_info['rangeMax'])
                    elif "macroMapping" in parent[key] and "rangeMax" in parent[key]["macroMapping"]:
                        # Remove rangeMax if it exists and the update value is empty
                        del parent[key]["macroMapping"]["rangeMax"]
                    
                    # Track this parameter as updated
                    updated_params.append(param_name)
        
        # Function to find and update parameter mappings (for parameters without direct paths)
        def update_parameter_mappings(data, path=""):
            if isinstance(data, dict):
                # Check if this is a parameter that matches one we want to update
                param_name = path.split(".")[-1] if path else ""
                
                # Debug: Print all parameters we find
                if path.endswith("parameters"):
                    for key in data.keys():
                        if key != "Enabled" and not key.startswith("Macro"):
                            print(f"Found parameter: {key} at path: {path}.{key}")
                
                for macro_index, update_info in parameter_updates.items():
                    # Skip parameters that have direct paths (already processed)
                    if update_info.get('parameter_path'):
                        continue
                        
                    if param_name == update_info.get('parameter'):
                        print(f"Found parameter to update: {param_name} at path: {path}")
                        
                        # Remove existing mapping if parameter is already mapped to a different macro
                        if param_name in mapped_parameters and mapped_parameters[param_name]['macro_index'] != macro_index:
                            remove_existing_mapping(param_name)
                        
                        # Get the parent object and key to update the parameter
                        parent_path = path.rsplit(".", 1)[0] if "." in path else ""
                        parent = get_object_at_path(preset_data, parent_path)
                        key = path.split(".")[-1]
                        
                        print(f"Parent path: {parent_path}, Key: {key}, Parent exists: {parent is not None}")
                        
                        if parent and key in parent:
                            print(f"Parameter value: {parent[key]}, Type: {type(parent[key])}")
                            # If this is a simple value (not an object with a value property)
                            if not isinstance(parent[key], dict) or "value" not in parent[key]:
                                # Store the original value
                                original_value = parent[key]
                                
                                # Replace with an object that has value and macroMapping
                                parent[key] = {
                                    "value": original_value,
                                    "macroMapping": {
                                        "macroIndex": macro_index
                                    }
                                }
                            else:
                                # It's already an object with a value property
                                # Create macroMapping if it doesn't exist
                                if "macroMapping" not in parent[key]:
                                    parent[key]["macroMapping"] = {}
                                
                                # Set the macro index
                                parent[key]["macroMapping"]["macroIndex"] = macro_index
                            
                            # Add range values if provided
                            if update_info.get('rangeMin') is not None and update_info.get('rangeMin') != "":
                                parent[key]["macroMapping"]["rangeMin"] = float(update_info['rangeMin'])
                            elif "macroMapping" in parent[key] and "rangeMin" in parent[key]["macroMapping"]:
                                # Remove rangeMin if it exists and the update value is empty
                                del parent[key]["macroMapping"]["rangeMin"]
                                
                            if update_info.get('rangeMax') is not None and update_info.get('rangeMax') != "":
                                parent[key]["macroMapping"]["rangeMax"] = float(update_info['rangeMax'])
                            elif "macroMapping" in parent[key] and "rangeMax" in parent[key]["macroMapping"]:
                                # Remove rangeMax if it exists and the update value is empty
                                del parent[key]["macroMapping"]["rangeMax"]
                            
                            # Track this parameter as updated
                            updated_params.append(param_name)
                
                # Recursively search in nested dictionaries
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    update_parameter_mappings(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    update_parameter_mappings(item, f"{path}[{i}]")
        
        # Update parameter mappings
        update_parameter_mappings(preset_data)
        
        # Write the updated preset back to the file
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {
            'success': True,
            'message': f"Updated {len(updated_params)} parameter mappings: {', '.join(updated_params)}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error updating parameter mappings: {e}"
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
