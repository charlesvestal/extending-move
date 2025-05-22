# Extending Move

This guide explains how to add new features to the Move webserver. Move follows a modular structure, with each feature comprising three components:

- **Core Logic**: Business logic (e.g., audio processing) in `core/`
- **Web Handler**: HTTP request handling in `handlers/`
- **HTML Template**: User interface in `templates/`

## Project Structure

```
extending-move/
├── move-webserver.py      # Main webserver with routing and request handling
├── core/                  # Core functionality implementations
│   ├── chord_handler.py         # Chord generation and pitch-shifting
│   ├── slice_handler.py         # Sample slicing and kit creation
│   ├── refresh_handler.py       # Library refresh via D-Bus
│   ├── reverse_handler.py       # WAV file reversal
│   ├── time_stretch_handler.py      # Time-stretching (with WSOLA/Phase-vocoder & repitch options)
│   ├── restore_handler.py       # Move Set restoration
│   ├── drum_rack_inspector.py   # Preset inspection and modification
│   └── synth_preset_inspector_handler.py  # Synth preset macro management
├── handlers/              # Web request handlers
│   ├── base_handler.py                    # Base handler with shared functionality
│   ├── chord_handler_class.py             # Chord generation interface
│   ├── slice_handler_class.py             # Slice kit creation interface
│   ├── refresh_handler_class.py           # Library refresh interface
│   ├── reverse_handler_class.py           # WAV reversal interface
│   ├── restore_handler_class.py           # Move Set restoration interface
│   ├── drum_rack_inspector_handler_class.py  # Preset inspection interface
│   ├── synth_preset_inspector_handler_class.py  # Synth macro management interface
│   └── file_placer_handler_class.py       # File upload and placement
├── templates/             # HTML templates and UI components
│   ├── index.html                # Main navigation with tab system
│   ├── chord.html               # Chord generation interface
│   ├── slice.html               # Waveform slicing interface
│   ├── reverse.html             # File selection with AJAX
│   ├── refresh.html             # Simple action template
│   ├── restore.html             # File upload with options
│   ├── drum_rack_inspector.html # Grid layout with actions
│   └── synth_preset_inspector.html # Synth macro management interface
├── examples/              # Example files for testing and development
│   ├── Track Presets/          # Sample presets organized by instrument type
│   │   ├── Drift/              # Drift instrument presets
│   │   ├── Wavetable/          # Wavetable instrument presets
│   │   ├── drumRack/           # Drum rack presets
│   │   └── melodicSampler/     # Melodic sampler presets
│   └── test scripts            # Various test scripts
└── utility-scripts/       # Installation and management scripts
    ├── install-on-move.sh     # Initial setup script
    ├── update-on-move.sh      # Update deployment script
    └── restart-webserver.sh   # Server management script
```

Each feature should follow this structure precisely:
- Core logic: `core/feature_name_handler.py`
- Handler class: `handlers/feature_name_handler_class.py`
- UI template: `templates/feature_name.html`

## Core Components

### 1. Core Handlers
Core handlers implement the main functionality of each feature. They should:
- Focus on core logic without web-specific code
- Handle file operations and data processing
- Return structured results with success/failure status
- Include comprehensive error handling

Example core handler structure:
```python
def process_feature(param1, param2):
    """
    Main function implementing feature logic.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        dict with keys:
        - success: bool indicating success/failure
        - message: Status or error message
        - Additional result data as needed
    """
    try:
        # Implementation
        return {
            'success': True,
            'message': 'Operation completed',
            'data': result_data
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }
```

### 2. Web Handlers
Web handlers manage HTTP requests and interface with core functionality. They should:
- Inherit from BaseHandler
- Handle form validation and file uploads
- Call core functions for processing
- Format responses consistently
- Clean up temporary files

Example web handler structure:
```python
from handlers.base_handler import BaseHandler
from core.your_feature import process_feature

class YourFeatureHandler(BaseHandler):
    def handle_post(self, form):
        """Handle POST request for feature."""
        try:
            # Validate form data
            if 'required_field' not in form:
                return self.format_error_response(
                    "Missing required field"
                )
                
            # Handle file upload if needed
            if 'file' in form:
                success, filepath = self.handle_file_upload(form)
                if not success:
                    return self.format_error_response(
                        "File upload failed"
                    )
            
            # Process using core functionality
            result = process_feature(
                form.getvalue('param1'),
                filepath
            )
            
            # Clean up and return result
            self.cleanup_upload(filepath)
            return self.format_success_response(
                result['message'],
                additional_data=result.get('data')
            )
            
        except Exception as e:
            return self.format_error_response(str(e))
```

### 3. Templates
Templates define the user interface for each feature. They should:
- Include only feature content (no HTML structure)
- Use consistent styling from style.css
- Handle both success and error states
- Support dynamic content updates

Example template structures:

1. Simple Action Template:
```html
<h2>Your Feature</h2>
{message_html}
<form method="post">
    <input type="hidden" name="action" value="your_action"/>
    <button type="submit">Perform Action</button>
</form>
```

2. File Upload Template:
```html
<h2>Your Feature</h2>
{message_html}
<form method="post" enctype="multipart/form-data">
    <input type="hidden" name="action" value="your_action"/>
    
    <label for="file">Select file:</label>
    <input type="file" name="file" accept=".wav" required/>
    
    <label for="option">Processing option:</label>
    <select name="option" required>
        {{ options }}
    </select>
    
    <button type="submit">Process File</button>
</form>
```

3. Interactive Template:
```html
<h2>Your Feature</h2>
{message_html}
<form method="post" id="featureForm">
    <input type="hidden" name="action" value="your_action"/>
    
    <div id="interactive-container"></div>
    
    <div class="controls">
        <button type="button" onclick="updatePreview()">
            Update Preview
        </button>
        <button type="submit">Process</button>
    </div>
</form>

<script>
    document.addEventListener('DOMContentLoaded', initializeFeature);
    
    function initializeFeature() {
        // Setup interactive elements
    }
    
    function updatePreview() {
        // Update UI based on user input
    }
</script>
```

## Move-Specific Details

### File Locations
Move uses specific directories for different file types:
```
/data/UserData/UserLibrary/
├── Samples/              # WAV files
│   └── Preset Samples/   # Preset-specific samples
└── Track Presets/        # Move presets (.ablpreset)
```

### Preset Format
Move presets follow the schema at http://tech.ableton.com/schema/song/1.5.1/devicePreset.json:

1. Basic Structure:
```json
{
  "$schema": "http://tech.ableton.com/schema/song/1.5.1/devicePreset.json",
  "kind": "instrumentRack",
  "name": "preset_name",
  "chains": [...]
}
```

2. Sample References:
```json
"sampleUri": "ableton:/user-library/Samples/Preset%20Samples/sample.wav"
```

3. Macro Mappings:
```json
"Parameter_Name": {
  "value": 0.5,
  "macroMapping": {
    "macroIndex": 0,
    "rangeMin": 0.0,
    "rangeMax": 1.0
  }
}
```

### Library Management
After modifying files:
1. Place files in correct directories
2. Use D-Bus to refresh library:
```python
subprocess.run([
    "dbus-send",
    "--system",
    "--type=method_call",
    "--dest=com.ableton.move",
    "--print-reply",
    "/com/ableton/move/browser",
    "com.ableton.move.Browser.refreshCache"
])
```

## Adding a New Feature

Follow these steps to add a new feature called `your_feature`:

### Step 1: Core Logic
Create `core/your_feature_handler.py` with a function for your main logic:

```python
def your_feature_logic(input_param1, input_param2):
    try:
        # Implement core logic here
        result = ...  # your result data
        return {'success': True, 'data': result, 'message': 'Operation succeeded'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
```

### Step 2: Web Handler
Create `handlers/your_feature_handler_class.py` inheriting from `BaseHandler`:

```python
from handlers.base_handler import BaseHandler
from core.your_feature_handler import your_feature_logic

class YourFeatureHandler(BaseHandler):
    def handle_post(self, form):
        # Validate form input
        if 'param1' not in form:
            return self.format_error_response('Missing required parameter: param1')

        # Process logic
        result = your_feature_logic(form.getvalue('param1'), form.getvalue('param2'))

        # Handle response
        if result['success']:
            return self.format_success_response(result['message'], additional_data=result.get('data'))
        else:
            return self.format_error_response(result['message'])
```

### Step 3: UI Template
Create `templates/your_feature.html` to render your UI:

```html
<h2>Your Feature</h2>
{message_html}
<form method="post">
    <input type="text" name="param1" required />
    <input type="text" name="param2" />
    <button type="submit">Submit</button>
</form>
```

### Step 4: Routing
In `move-webserver.py`, register your routes:

```python
from handlers.your_feature_handler_class import YourFeatureHandler

class MyServer(BaseHTTPRequestHandler):
    your_feature_handler = YourFeatureHandler()

    @route_handler.get("/your-feature", "your_feature.html")
    def handle_your_feature_get(self):
        return {}

    @route_handler.post("/your-feature")
    def handle_your_feature_post(self, form):
        return self.your_feature_handler.handle_post(form)
```

### Step 5: Tab Integration
In `templates/index.html`, add a tab entry:

```html
<button class="tablinks" onclick="openTab(event, 'YourFeature')">Your Feature</button>
<div id="YourFeature" class="tabcontent"></div>
```

### Example: Time Stretch Feature

Demonstrates adding audio time-stretching functionality:

- Core (`core/time_stretch_handler.py`):
  - Implements `time_stretch_wav` for WSOLA, phase-vocoder, and repitch.

- Web Handler (`handlers/drum_rack_inspector_handler_class.py`):
  - Processes form inputs (BPM, measures, preserve pitch, algorithm).
  - Calls the core function and updates presets.

- Template (`templates/drum_rack_inspector.html`):
  - Provides a modal with form inputs and dynamic updates.

- JavaScript (`static/main.js`):
  - AJAX form submission and waveform updates.

Dependencies added: `audiotsm`, `librosa`, `soundfile`.

## Form Submission Approach

The Move Extended application uses a tab-based interface where each feature is loaded in a tab without requiring full page reloads. This approach keeps users on the current page when submitting forms, providing a smoother user experience. Understanding this approach is essential when creating new features.

### Tab-Based Interface

The application uses a tab system defined in `index.html` where:

1. Each feature has a tab button and a content container
2. When a tab is clicked, the `openTab` function is called
3. Tab content is dynamically loaded via AJAX
4. Form handlers are attached to enable AJAX form submission

```html
<!-- Tab buttons -->
<button class="tablinks" onclick="openTab(event, 'YourFeature')">Your Feature</button>

<!-- Tab content container -->
<div id="YourFeature" class="tabcontent">
    <!-- Content loaded dynamically -->
</div>
```

### AJAX Form Submission

Forms are submitted asynchronously to prevent page navigation:

1. The `attachFormHandler` function intercepts form submissions
2. The default form submission behavior is prevented with `event.preventDefault()`
3. Form data is submitted via the fetch API
4. The response updates the tab content without page navigation
5. Event handlers are re-attached to maintain interactivity

```javascript
// Simplified version of the form submission process
form.addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData(form);
    
    const response = await fetch(url, {
        method: form.method,
        body: formData
    });
    
    const result = await response.text();
    document.getElementById(tabName).innerHTML = result;
    
    // Re-attach event handlers
    attachFormHandler(tabName);
});
```

### Form Structure Requirements

To ensure forms work with this system:

1. **Form Structure**
   - Use standard HTML forms with `method="POST"` and appropriate `action` attributes
   - Include all form fields within the form element
   - Use hidden inputs for action identifiers

2. **Handler Responses**
   - Return complete HTML for the tab content
   - Include success/error messages
   - Preserve form state where appropriate

3. **Form Example**
   ```html
   <form method="POST" action="/your-feature">
       <input type="hidden" name="action" value="your_action">
       
       <!-- Form fields -->
       <input type="text" name="field_name">
       <select name="option">
           {{ options }}
       </select>
       
       <!-- Submit button -->
       <button type="submit">Process</button>
   </form>
   ```

### Multiple Actions in One Form

For forms that need multiple submit buttons with different actions:

1. Use a hidden input for the action value
2. Update this value via JavaScript when different buttons are clicked

```html
<form method="POST" action="/your-feature" id="feature-form">
    <input type="hidden" name="action" id="action-input" value="default_action">
    
    <!-- Form fields -->
    <input type="text" name="field_name">
    
    <!-- Buttons that set different actions -->
    <button type="submit" onclick="document.getElementById('action-input').value='action1'">
        Action 1
    </button>
    <button type="submit" onclick="document.getElementById('action-input').value='action2'">
        Action 2
    </button>
</form>
```

### Handler Implementation

Your handler should:

1. Process the form data
2. Return complete HTML for the tab content
3. Include appropriate messages and updated form elements

```python
def handle_post(self, form):
    action = form.getvalue('action')
    
    if action == 'action1':
        # Process action1
        result = process_action1(form)
    elif action == 'action2':
        # Process action2
        result = process_action2(form)
    else:
        return self.format_error_response("Unknown action")
    
    # Return complete HTML with message and updated form elements
    return {
        "message": result['message'],
        "message_type": "success",
        "form_html": self.generate_form_html(result)
    }
```

## Best Practices

1. **Code Organization**
   - Separate core logic from web handling
   - Use clear, descriptive names
   - Follow established patterns
   - Add comprehensive comments

2. **Error Handling**
   - Use try/except blocks consistently
   - Provide clear error messages
   - Clean up temporary files
   - Handle edge cases

3. **User Interface**
   - Provide clear feedback
   - Use consistent styling
   - Include form validation
   - Show loading states

4. **File Management**
   - Clean up temporary files
   - Use absolute paths
   - Handle name collisions
   - Follow Move's structure

5. **Move Integration**
   - Follow preset format
   - Use correct URI formats
   - Refresh library after changes
   - Test thoroughly

6. **JavaScript**
   - Initialize after loading
   - Clean up on tab switch
   - Handle async operations
   - Provide loading indicators

7. **Working with Presets**
   - Understand the structure of different preset types (Drift, drumRack, etc.)
   - Handle macro mappings carefully
   - Preserve original parameter values when removing mappings
   - Test with various preset types

8. **Using the Examples Directory**
   - Use example presets for testing
   - Organize new examples by instrument type
   - Include representative samples of different parameter configurations
   - Document any special cases or edge conditions

## Testing

1. **Core Functionality**
   - Test with various inputs
   - Verify error handling
   - Check edge cases
   - Test file operations

2. **Web Interface**
   - Test form submissions
   - Verify file uploads
   - Check error displays
   - Test async operations

3. **Move Integration**
   - Test preset generation
   - Verify library updates
   - Check file permissions
   - Test on actual device

4. **Preset Compatibility**
   - Test with different preset types
   - Verify parameter mappings work correctly
   - Check for compatibility issues between versions
   - Test with both simple and complex presets

## Conclusion

Following these guidelines ensures:
- Consistent code organization
- Reliable error handling
- Clean user interface
- Proper Move integration
- Maintainable features

Remember to:
- Keep core logic separate
- Handle errors gracefully
- Test thoroughly
- Clean up resources
- Follow Move's conventions
