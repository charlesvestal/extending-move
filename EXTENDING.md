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
├── templates/             # HTML templates for each feature
│   ├── index.html        # Main navigation page with tab system
│   ├── style.css         # Shared styles
│   └── feature.html      # Feature-specific templates
└── utility-scripts/       # Utility scripts for installation and management
    ├── install-on-move.sh    # Initial setup and installation
    ├── update-on-move.sh     # Update Move with latest changes
    └── restart-webserver.sh   # Restart the Move webserver
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

### 3. Create Feature Template

Add a new template file in the `templates` directory named `your_feature.html`. The template system uses dynamic loading within tabs, so your template should ONLY include the feature's content without any HTML structure (no html, head, or body tags).

Here are examples of both simple and complex templates:

1. Simple Template (like refresh.html):
```html
<h2>Your Feature Title</h2>
{message_html}
<form method="post">
    <input type="hidden" name="action" value="your_action"/>
    <input type="submit" value="Perform Action"/>
</form>
```

2. Template with File Selection (like reverse.html):
```html
<h2>Your Feature Title</h2>
{message_html}
<form method="post">
    <input type="hidden" name="action" value="your_action"/>
    
    <label for="file_select">Select file:</label>
    <select id="file_select" name="file_select" required>
        <option value="" disabled selected>--Select a file--</option>
        {{ options }}
    </select>
    
    <button type="submit">Process File</button>
</form>

<script>
    // Feature-specific JavaScript
    function validateForm() {
        // Your validation logic
    }
</script>
```

3. Complex Interactive Template (like slice.html):
```html
<h2>Your Feature Title</h2>
{message_html}
<form enctype="multipart/form-data" method="post">
    <input type="hidden" name="action" value="your_action"/>
    
    <!-- File input with preview -->
    <label for="file">Select file:</label>
    <input id="file" name="file" type="file" accept=".wav" required/>
    
    <!-- Interactive controls -->
    <label for="num_items">Number of items:</label>
    <input id="num_items" name="num_items" type="number" 
           min="1" max="16" value="16" required/>
    
    <!-- Multiple submit options -->
    <button type="submit" onclick="setMode('download')">
        Download Result
    </button>
    <button type="submit" onclick="setMode('process')">
        Process Directly
    </button>
</form>

<!-- Interactive UI container -->
<div id="preview-container" style="width: 100%; height: 128px;"></div>
```

Key points for templates:
- Omit all HTML structure tags (html, head, body) - content is loaded into tabs
- Include the `{message_html}` placeholder for displaying messages
- Use proper form encoding if handling file uploads
- Add a hidden action field to identify the operation
- Include any feature-specific JavaScript in the template
- Use consistent styling (styles are loaded from shared style.css)

For templates with dynamic content:
- Use `{{ variable }}` syntax for server-injected content
- Keep JavaScript scoped to the feature's functionality
- Initialize UI components after content is loaded
- Clean up resources when switching tabs

### 4. Update index.html

Add your feature to the tab system in `index.html`:

1. Add a tab button:
```html
<div class="tab">
    <!-- Existing tabs -->
    <button class="tablinks" onclick="openTab(event, 'YourFeature')">
        Your Feature
    </button>
</div>
```

2. Add a tab content container:
```html
<div id="YourFeature" class="tabcontent">
    <!-- Content will be loaded here dynamically -->
</div>
```

3. If your feature needs special initialization:
```javascript
function openTab(evt, tabName) {
    // Existing tab opening code...
    
    // Add your feature's initialization
    if (tabName === 'YourFeature') {
        initializeYourFeature();
    }
}
```

### 5. Update move-webserver.py

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

## JavaScript Integration

The webserver uses a dynamic content loading system with these key components:

1. Tab System:
```javascript
function openTab(evt, tabName) {
    // Hide all tab content
    var tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    
    // Show selected tab
    document.getElementById(tabName).style.display = "block";
    
    // Load content dynamically
    fetchContent(tabName);
}
```

2. Dynamic Content Loading:
```javascript
async function fetchContent(tabName) {
    const response = await fetch(`/${tabName.toLowerCase()}`);
    const data = await response.text();
    document.getElementById(tabName).innerHTML = data;
}
```

3. Form Handling:
```javascript
function attachFormHandler(tabName) {
    const form = document.querySelector(`#${tabName} form`);
    if (form) {
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(form);
            // Handle form submission...
        });
    }
}
```

### Example: Interactive Features

For features requiring interactive elements (like the Slice Kit's waveform):

1. Initialize in the tab system:
```javascript
if (tabName === 'YourFeature') {
    initializeFeature();
}
```

2. Clean up when switching tabs:
```javascript
function cleanupFeature() {
    // Remove event listeners
    // Clean up UI components
}
```

3. Handle dynamic updates:
```javascript
function updateFeatureUI() {
    // Update UI based on user interactions
}
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

7. **JavaScript Integration**
   - Initialize features after dynamic loading
   - Clean up resources when switching tabs
   - Use event delegation for dynamic content
   - Handle form submissions asynchronously
   - Provide loading indicators for async operations

8. **Template Structure**
   - Keep templates focused on feature content
   - Include necessary JavaScript in templates
   - Use consistent form structures
   - Handle both success and error states
   - Support dynamic UI updates

## Conclusion

Following these guidelines will help maintain consistency and reliability when extending the Move webserver. The separation between core functionality and web handling makes the code more maintainable and easier to test. Remember to:

- Keep core logic in core/ directory
- Put web handling in handlers/ directory
- Create clear and user-friendly templates
- Handle errors gracefully
- Test thoroughly before deployment
- Follow Move's file and preset formats
- Support dynamic content loading
- Clean up resources properly
