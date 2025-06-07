#!/usr/bin/env python3
import os
import json
import logging
from core.cache_manager import get_cache, set_cache

logger = logging.getLogger(__name__)

def extract_available_parameters(preset_path):
    """
    Extract available parameters from drift or wavetable devices in a preset file.
    
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
        
        # Dictionary to store synth device paths
        synth_device_paths = set()
        
        # First, find all drift and wavetable devices
        def find_synth_devices(data, path=""):
            if isinstance(data, dict):
                # Check if this is a drift device
                if data.get('kind') == 'drift':  # Only look for drift devices
                    synth_device_paths.add(path)
                    logger.debug("Found %s device at path: %s", data.get('kind'), path)
                
                # Recursively search in nested dictionaries
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    find_synth_devices(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_synth_devices(item, f"{path}[{i}]")
        
        # Find all synth devices
        find_synth_devices(preset_data)
        
        # Function to recursively find parameters in synth devices
        def find_parameters(data, path=""):
            if isinstance(data, dict):
                # If this is a parameters object
                if path.endswith("parameters"):
                    # Check if this parameters object belongs to a synth device
                    is_synth_parameter = False
                    for device_path in synth_device_paths:
                        if path.startswith(device_path) or device_path.startswith(path.rsplit('.parameters', 1)[0]):
                            is_synth_parameter = True
                            break
                    
                    if is_synth_parameter:
                        # Add all keys that aren't "Enabled" or start with "Macro"
                        for key in data.keys():
                            if key != "Enabled" and not key.startswith("Macro"):
                                parameters.add(key)
                                parameter_paths[key] = f"{path}.{key}"
                                logger.debug("Adding synth parameter: %s at path: %s.%s", key, path, key)
                
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


def extract_parameter_values(preset_path):
    """Return all parameter names and their values from drift presets."""
    try:
        with open(preset_path, "r") as f:
            preset_data = json.load(f)

        parameter_values = {}
        synth_device_paths = set()

        def find_synth_devices(data, path=""):
            if isinstance(data, dict):
                if data.get("kind") == "drift":
                    synth_device_paths.add(path)
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    find_synth_devices(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_synth_devices(item, f"{path}[{i}]")

        find_synth_devices(preset_data)

        def find_parameters(data, path=""):
            if isinstance(data, dict):
                if path.endswith("parameters"):
                    is_synth_parameter = False
                    for device_path in synth_device_paths:
                        if path.startswith(device_path) or device_path.startswith(path.rsplit(".parameters", 1)[0]):
                            is_synth_parameter = True
                            break
                    if is_synth_parameter:
                        for key, val in data.items():
                            if key != "Enabled" and not key.startswith("Macro"):
                                if isinstance(val, dict) and "value" in val:
                                    parameter_values[key] = val["value"]
                                else:
                                    parameter_values[key] = val
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    find_parameters(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_parameters(item, f"{path}[{i}]")

        find_parameters(preset_data)

        params = [
            {"name": name, "value": parameter_values[name]}
            for name in sorted(parameter_values.keys())
        ]

        return {
            "success": True,
            "parameters": params,
            "message": f"Found {len(params)} parameters",
        }

    except Exception as exc:
        return {
            "success": False,
            "message": f"Error extracting parameter values: {exc}",
            "parameters": [],
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
        def find_and_update_macros(data, path=""):
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
                                # Skip top-level parameters (they should remain as simple values)
                                if path == "":
                                    # For top-level parameters, we don't modify the structure
                                    # They should remain as simple values
                                    continue
                                
                                # For device parameters (not top-level), we can add customName
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
                    new_path = f"{path}.{key}" if path else key
                    if isinstance(value, dict):
                        updated_count += find_and_update_macros(value, new_path)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                updated_count += find_and_update_macros(item, f"{new_path}[{i}]")
            
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
        
        # Debug: Log parameter updates
        logger.debug("Parameter updates: %s", parameter_updates)
        
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
                    logger.debug(
                        "Removing existing mapping for %s from macro %s",
                        param_name,
                        mapping_info['macro_index'],
                    )
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
                
                logger.debug("Using direct path for parameter %s: %s", param_name, param_path)
                logger.debug("Parent path: %s", parent_path)
                
                # Remove existing mapping if parameter is already mapped to a different macro
                if param_name in mapped_parameters and mapped_parameters[param_name]['macro_index'] != macro_index:
                    remove_existing_mapping(param_name)
                
                parent = get_object_at_path(preset_data, parent_path)
                key = param_path.split(".")[-1]
                
                if parent and key in parent:
                    logger.debug("Found parameter using direct path: %s", param_name)
                    logger.debug("Parameter value: %s, Type: %s", parent[key], type(parent[key]))
                    
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
                            logger.debug("Found parameter: %s at path: %s.%s", key, path, key)
                
                for macro_index, update_info in parameter_updates.items():
                    # Skip parameters that have direct paths (already processed)
                    if update_info.get('parameter_path'):
                        continue
                        
                    if param_name == update_info.get('parameter'):
                        logger.debug("Found parameter to update: %s at path: %s", param_name, path)
                        
                        # Remove existing mapping if parameter is already mapped to a different macro
                        if param_name in mapped_parameters and mapped_parameters[param_name]['macro_index'] != macro_index:
                            remove_existing_mapping(param_name)
                        
                        # Get the parent object and key to update the parameter
                        parent_path = path.rsplit(".", 1)[0] if "." in path else ""
                        parent = get_object_at_path(preset_data, parent_path)
                        key = path.split(".")[-1]
                        
                        logger.debug(
                            "Parent path: %s, Key: %s, Parent exists: %s",
                            parent_path,
                            key,
                            parent is not None,
                        )
                        
                        if parent and key in parent:
                            logger.debug(
                                "Parameter value: %s, Type: %s",
                                parent[key],
                                type(parent[key]),
                            )
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

def delete_parameter_mapping(preset_path, param_path):
    """
    Delete a parameter mapping from a preset file.
    
    Args:
        preset_path: Path to the .ablpreset file
        param_path: Full path to the parameter to delete mapping from
        
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
    """
    try:
        # Load the preset file
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
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
        
        # Get the parent path and key
        parent_path = param_path.rsplit(".", 1)[0]
        key = param_path.split(".")[-1]
        
        # Get the parent object
        parent = get_object_at_path(preset_data, parent_path)
        
        if parent and key in parent:
            # Check if the parameter has a macroMapping
            if isinstance(parent[key], dict) and "macroMapping" in parent[key]:
                # Store the original value
                original_value = parent[key].get("value")
                
                # Replace the object with just the value
                parent[key] = original_value
                
                # Write the updated preset back to the file
                with open(preset_path, 'w') as f:
                    json.dump(preset_data, f, indent=2)
                
                return {
                    'success': True,
                    'message': f"Deleted mapping for parameter {key}"
                }
            else:
                return {
                    'success': False,
                    'message': f"Parameter {key} does not have a macro mapping"
                }
        else:
            return {
                'success': False,
                'message': f"Parameter not found at path: {param_path}"
            }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error deleting parameter mapping: {e}"
        }

def scan_for_synth_presets():
    """Scan ``Track Presets`` for synth presets using a cache."""
    cache_key = "synth_presets"
    cached = get_cache(cache_key)
    if cached is not None:
        return {
            "success": True,
            "message": f"Found {len(cached)} synth presets (cached)",
            "presets": cached,
        }

    try:
        presets_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(presets_dir) and os.path.exists("examples/Track Presets"):
            presets_dir = "examples/Track Presets"

        synth_presets = []

        # Function to recursively search for specific device types
        def has_device_type(data, device_types):
            if isinstance(data, dict):
                if data.get('kind') in device_types:
                    return data.get('kind')
                for v in data.values():
                    result = has_device_type(v, device_types)
                    if result:
                        return result
            elif isinstance(data, list):
                for item in data:
                    result = has_device_type(item, device_types)
                    if result:
                        return result
            return None

        # Scan all .ablpreset files in all subdirectories
        for root, dirs, files in os.walk(presets_dir):
            for filename in files:
                if filename.endswith('.ablpreset'):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r') as f:
                            preset_data = json.load(f)

                        # Check if preset contains a drift device
                        device_type = has_device_type(preset_data, ['drift'])  # Only look for drift devices
                        if device_type:
                            preset_name = os.path.splitext(filename)[0]
                            rel = os.path.relpath(filepath, presets_dir)
                            rel_no_ext = os.path.splitext(rel)[0]
                            synth_presets.append({
                                'name': preset_name,
                                'path': filepath,
                                'display_path': rel_no_ext,
                                'type': device_type
                            })
                    except Exception as e:
                        logger.warning("Could not parse preset %s: %s", filename, e)
                        continue

        set_cache(cache_key, synth_presets)
        return {
            "success": True,
            "message": f"Found {len(synth_presets)} synth presets",
            "presets": synth_presets,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error scanning presets: {e}",
            "presets": [],
        }
