# Extending Move

This guide explains how to extend the Move webserver with new features. The webserver follows a modular architecture where each feature consists of:

1. Core functionality in the core/ directory
2. A web handler in the handlers/ directory
3. An HTML template in the templates/ directory

## Project Structure

```
extending-move/
├── move-webserver.py      # Main webserver that handles routing and requests
├── core/                  # Core functionality for each feature
│   ├── slice_handler.py   # Core slicing functionality
│   ├── refresh_handler.py # Core refresh functionality
│   └── reverse_handler.py # Core WAV reversal functionality
├── handlers/              # Web handlers for each feature
│   ├── base_handler.py    # Base class for all handlers
│   ├── slice_handler_class.py   # Web interface for slicing
│   ├── refresh_handler_class.py # Web interface for refresh
│   └── reverse_handler_class.py # Web interface for reversal
└── templates/             # HTML templates for each feature
    ├── index.html        # Main navigation page
    ├── style.css         # Shared styles
    └── feature.html      # Feature-specific templates
```

## Move-Specific Details

### File Locations

Move uses specific directories for different types of files:

```
/data/UserData/UserLibrary/
├── Samples/              # WAV files and other audio samples
│   └── Preset Samples/   # Samples used by presets
└── Track Presets/        # Move preset files (.ablpreset)
```

### Preset Format

Move presets (.ablpreset files) follow the schema at http://tech.ableton.com/schema/song/1.4.4/devicePreset.json. Key components include:

1. Instrument Racks:
   ```json
   {
     "$schema": "http://tech.ableton.com/schema/song/1.4.4/devicePreset.json",
     "kind": "instrumentRack",
     "name": "preset_name",
     "chains": [...]
   }
   ```

2. Device References:
   ```json
   {
     "presetUri": null,
     "kind": "deviceType",  // e.g., "drumCell", "reverb"
     "parameters": {...},
     "deviceData": {...}
   }
   ```

3. Sample References:
   ```json
   "sampleUri": "ableton:/user-library/Samples/Preset%20Samples/sample.wav"
   ```

### Bundle Format

When creating downloadable presets, use the .ablpresetbundle format:
- ZIP file containing:
  - Preset.ablpreset at root
  - Samples/ directory with referenced WAV files
- Use URI-encoded filenames in sample references

### Library Management

After modifying files in Move's library:
1. Place files in correct directories
2. Use D-Bus to refresh the library cache:
   ```python
   dbus-send --system --type=method_call \
             --dest=com.ableton.move \
             --print-reply \
             /com/ableton/move/browser \
             com.ableton.move.Browser.refreshCache
   ```

## Adding a New Feature

Here's how to add a new feature to the Move webserver:

### 1. Create Core Functionality

Create a new Python file in the `core` directory named `your_feature_handler.py`. This file should contain the core logic for your feature.

Example structure for a core handler:

```python
#!/usr/bin/env python3

def process_your_feature(param1, param2, ...):
    """
    Main function that implements your feature's logic.
    
    Parameters:
    - param1: Description of param1
    - param2: Description of param2
    
    Returns:
    A dictionary with keys:
    - 'success': bool
    - 'message': str
    - Additional keys as needed
    """
    try:
        # Your implementation here
        return {
            'success': True,
            'message': 'Operation completed successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }
```

Key points for core handlers:
- Focus on core functionality without web-specific logic
- Use descriptive function names that indicate the action
- Include comprehensive docstrings
- Return dictionaries with at least 'success' and 'message' keys
- Implement proper error handling
- Add any necessary helper functions

### 2. Create a Web Handler

Create a new Python file in the `handlers` directory named `your_feature_handler_class.py`. This class will handle web-specific logic and inherit from BaseHandler.

Example structure for a web handler:

```python
#!/usr/bin/env python3
import cgi
from handlers.base_handler import BaseHandler
from core.your_feature_handler import process_your_feature

class YourFeatureHandler(BaseHandler):
    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for your feature."""
        # Validate action
        valid, error_response = self.validate_action(form, "your_action")
        if not valid:
            return error_response

        try:
            # Extract parameters from form
            param1 = form.getvalue('param1')
            
            # Handle file upload if needed
            if 'file' in form:
                success, filepath, error_response = self.handle_file_upload(form)
                if not success:
                    return error_response
                
                # Process the file...
                self.cleanup_upload(filepath)
            
            # Call core functionality
            result = process_your_feature(param1)
            
            if result['success']:
                return self.format_success_response(result['message'])
            else:
                return self.format_error_response(result['message'])
                
        except Exception as e:
            return self.format_error_response(f"Error processing request: {str(e)}")
```

Key points for web handlers:
- Inherit from BaseHandler
- Handle form validation and file uploads
- Use core functionality for processing
- Format responses consistently
- Clean up temporary files

### 3. Create an HTML Template

Add a new template file in the `templates` directory named `your_feature.html`.

Example template structure:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Your Feature - Move</title>
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Your Feature</h1>
        
        <!-- Display messages (required for all templates) -->
        {message_html}
        
        <form action="/your-feature" method="post" enctype="multipart/form-data">
            <!-- Add your form inputs -->
            <input type="hidden" name="action" value="your_action">
            
            <!-- Example inputs -->
            <input type="text" name="param1" required>
            <input type="file" name="file" accept=".wav">
            
            <button type="submit">Process</button>
        </form>
        
        <p><a href="/">Back to Home</a></p>
    </div>
</body>
</html>
```

Key points for templates:
- Include the shared stylesheet
- Always include the `{message_html}` placeholder for displaying messages
- Use semantic HTML and clear structure
- Include proper form encoding if handling file uploads
- Add a hidden action field to identify the operation
- Link back to the home page

### 4. Update move-webserver.py

Add your feature to the webserver using the decorator-based routing system:

```python
from handlers.your_feature_handler_class import YourFeatureHandler

# In MyServer class:
your_feature_handler = YourFeatureHandler()

@route_handler.get("/your-feature", "your_feature.html")
def handle_your_feature_get(self):
    return {}

@route_handler.post("/your-feature")
def handle_your_feature_post(self, form):
    return self.your_feature_handler.handle_post(form)
```

The routing system will automatically:
- Load and cache templates
- Handle HTTP responses
- Format messages
- Handle errors consistently

5. Update `index.html` to add a link to your feature:
```html
<a href="/your-feature" class="button">Your Feature</a>
```

## Best Practices

1. **Code Organization**
   - Keep core functionality separate from web handling
   - Use clear, descriptive names for files and functions
   - Follow the established directory structure
   - Add comments for complex logic

2. **Error Handling**
   - Use try/except blocks in both core and web handlers
   - Return clear error messages
   - Clean up temporary files in error cases
   - Handle both expected and unexpected errors

3. **User Interface**
   - Provide clear feedback for all actions
   - Use consistent styling with style.css
   - Include proper form validation
   - Show loading states for long operations

4. **Testing**
   - Test core functionality independently
   - Test web handling with various inputs
   - Verify error handling works correctly
   - Test file upload limits if applicable

5. **File Management**
   - Clean up temporary files after use
   - Use absolute paths for file operations
   - Handle file name collisions gracefully
   - Follow Move's directory structure

6. **Move Integration**
   - Follow Move's preset format
   - Use correct sample URI formats
   - Refresh library after modifications
   - Test with Move's file structure

## Conclusion

Following these guidelines will help maintain consistency and reliability when extending the Move webserver. The separation between core functionality and web handling makes the code more maintainable and easier to test. Remember to:

- Keep core logic in core/ directory
- Put web handling in handlers/ directory
- Create clear and user-friendly templates
- Handle errors gracefully
- Test thoroughly before deployment
- Follow Move's file and preset formats
