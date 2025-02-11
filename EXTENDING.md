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

## Conclusion

Following these guidelines will help maintain consistency and reliability when extending the Move webserver. The separation between core functionality and web handling makes the code more maintainable and easier to test. Remember to:

- Keep core logic in core/ directory
- Put web handling in handlers/ directory
- Create clear and user-friendly templates
- Handle errors gracefully
- Test thoroughly before deployment
