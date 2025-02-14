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
│   ├── slice_handler.py         # Sample slicing and kit creation
│   ├── refresh_handler.py       # Library refresh functionality
│   ├── reverse_handler.py       # WAV file reversal
│   ├── restore_handler.py       # Move Set restoration
│   └── drum_rack_inspector.py   # Preset inspection and modification
├── handlers/              # Web handlers for each feature
│   ├── base_handler.py           # Base class for all handlers
│   ├── slice_handler_class.py    # Slice kit creation interface
│   ├── refresh_handler_class.py  # Library refresh interface
│   ├── reverse_handler_class.py  # WAV reversal interface
│   ├── restore_handler_class.py  # Move Set restoration interface
│   └── drum_rack_inspector_handler_class.py  # Preset inspection interface
├── templates/             # HTML templates for each feature
│   ├── index.html              # Main navigation page with tab system
│   ├── style.css              # Shared styles
│   ├── slice.html            # Complex interactive template with waveform
│   ├── reverse.html          # File selection with AJAX handling
│   ├── refresh.html          # Simple action template
│   ├── restore.html          # File upload with dynamic options
│   └── drum_rack_inspector.html  # Grid layout with multiple actions
└── utility-scripts/       # Utility scripts for installation and management
    ├── install-on-move.sh    # Initial setup and installation
    ├── update-on-move.sh     # Update Move with latest changes
    └── restart-webserver.sh   # Restart the Move webserver
```

Each feature typically consists of three components:
1. **Core Handler** (core/): Contains the core logic and functionality
   - File operations (e.g., slicing, reversing)
   - Preset manipulation (e.g., reading, modifying)
   - Library management
   
2. **Web Handler** (handlers/): Manages web interface and requests
   - Form handling and validation
   - File uploads
   - Response formatting
   
3. **Template** (templates/): Defines the user interface
   - Simple forms (e.g., refresh.html)
   - File selection (e.g., reverse.html)
   - Complex interactive UIs (e.g., slice.html)
   - Grid layouts (e.g., drum_rack_inspector.html)

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

2. Template with File Upload and Dynamic Options (like restore.html):
```html
<h2>Restore Move Set</h2>
{message_html}
<form action="/restore" method="post" enctype="multipart/form-data">
    <input type="hidden" name="action" value="restore_ablbundle"/>
    
    <label for="ablbundle">Select .ablbundle file:</label>
    <input type="file" name="ablbundle" accept=".ablbundle" required>
    
    <label for="mset_index">Restore to pad:</label>
    <select name="mset_index">
        {{ options }}  <!-- Dynamically populated with available pads -->
    </select>
    
    <label for="mset_color">Pad Color (1-26):</label>
    <input type="number" name="mset_color" min="1" max="26" value="1" required>
    
    <button type="submit">Upload & Restore</button>
</form>

<script>
    // Ensure first option is selected after form submission
    function initializeRestoreForm() {
        const select = document.querySelector('select[name="mset_index"]');
        if (select && select.options.length > 0 && !select.value) {
            select.selectedIndex = 0;
        }
    }
    
    // Initialize form when loaded
    document.addEventListener('DOMContentLoaded', initializeRestoreForm);
</script>
```

3. Template with File Selection and AJAX (like reverse.html):
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
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.querySelector('form');
        const submitButton = form.querySelector('button[type="submit"]');
        
        submitButton.addEventListener('click', function(event) {
            event.preventDefault();
            const fileSelect = document.getElementById('file_select');
            const selectedFile = fileSelect.value;
            if (!selectedFile) {
                alert('Please select a file.');
                return;
            }
            const confirmAction = confirm(`Are you sure you want to process "${selectedFile}"?`);
            if (confirmAction) {
                // Let the main.js AJAX handler take over
                form.dispatchEvent(new Event('submit'));
            }
        });
    });
</script>
```

3. Template with Grid Layout and Actions (like drum_rack_inspector.html):
```html
<h2>Your Feature Title</h2>
{message_html}

<form method="POST">
    <input type="hidden" name="action" value="select_item">
    <label for="item_select">Select Item:</label>
    <select name="item_select" id="item_select">
        {{ options }}
    </select>
</form>

<div class="grid-container">
    {{ grid_html }}
</div>

<!-- Example of dynamically generated grid cell -->
<div class="grid-cell">
    <div class="cell-info">
        <span class="cell-number">Cell 1</span>
    </div>
    <div class="preview-container" data-preview-path="{{ preview_path }}"></div>
    <div class="cell-actions">
        <a href="{{ download_path }}" class="action-button">Download</a>
        <form method="POST" action="/your-feature">
            <input type="hidden" name="action" value="process_item">
            <input type="hidden" name="item_path" value="{{ item_path }}">
            <button type="submit" class="action-button">Process</button>
        </form>
    </div>
</div>
```

4. Complex Interactive Template (like slice.html):
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
