# Extending Move

This guide explains how to extend the Move webserver with new features. The webserver follows a modular architecture where each feature consists of:

1. A handler file that contains the core logic
2. An HTML template for the web interface
3. Integration with the main webserver

## Project Structure

```
extending-move/
├── move-webserver.py      # Main webserver that handles routing and requests
├── templates/             # HTML templates for each feature
│   ├── index.html        # Main navigation page
│   ├── style.css         # Shared styles
│   └── feature.html      # Feature-specific templates
└── *_handler.py          # Handler files containing feature logic
```

## Adding a New Feature

Here's how to add a new feature to the Move webserver:

### 1. Create a Handler File

Create a new Python file named `your_feature_handler.py`. Handler files contain the core logic for your feature.

Example structure for a handler:

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

Key points for handlers:
- Use descriptive function names that indicate the action
- Include comprehensive docstrings
- Return dictionaries with at least 'success' and 'message' keys
- Implement proper error handling
- Add any necessary helper functions

### 2. Create an HTML Template

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

### 3. Update move-webserver.py

Modify `move-webserver.py` to integrate your feature:

1. Import your handler at the top:
```python
from your_feature_handler import process_your_feature
```

2. Add GET route in the `do_GET` method:
```python
elif self.path == "/your-feature":
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    with open(os.path.join("templates", "your_feature.html"), "r") as f:
        html_content = f.read().replace("{message_html}", "")
        self.wfile.write(bytes(html_content, "utf-8"))
```

3. Add POST handling in the `do_POST` method:
```python
elif action == "your_action" and self.path == "/your-feature":
    try:
        # Extract parameters from form
        param1 = form.getvalue('param1')
        
        # Handle file upload if needed
        if 'file' in form:
            file_field = form['file']
            if not file_field.filename:
                message = "No file uploaded"
                message_type = "error"
                self.respond_with_form(self.path, message, message_type)
                return
                
            # Process the file...
            
        # Call your handler
        result = process_your_feature(param1)
        
        if result['success']:
            message = result['message']
            message_type = "success"
        else:
            message = result['message']
            message_type = "error"
            
        self.respond_with_form(self.path, message, message_type)
        
    except Exception as e:
        self.respond_with_form(self.path, f"Error: {str(e)}", "error")
```

4. Update `index.html` to add a link to your feature:
```html
<a href="/your-feature" class="button">Your Feature</a>
```

## Best Practices

1. **Error Handling**
   - Always use try/except blocks in handlers
   - Return clear error messages
   - Handle both expected and unexpected errors

2. **Code Organization**
   - Keep handler logic separate from web server code
   - Use clear, descriptive function and variable names
   - Add comments for complex logic
   - Include docstrings for all functions

3. **User Interface**
   - Provide clear feedback for all actions
   - Use consistent styling with style.css
   - Include proper form validation
   - Show loading states for long operations

4. **Testing**
   - Test your feature with various inputs
   - Verify error handling works correctly
   - Check both success and failure cases
   - Test file upload limits if applicable

## Example: Adding a Simple Feature

Here's a complete example of adding a simple feature that reverses text:

1. Create `text_handler.py`:
```python
#!/usr/bin/env python3

def reverse_text(text):
    """
    Reverses the input text.
    
    Parameters:
    - text: String to reverse
    
    Returns:
    Dictionary with success status and result
    """
    try:
        reversed_text = text[::-1]
        return {
            'success': True,
            'message': 'Text reversed successfully',
            'result': reversed_text
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error reversing text: {str(e)}'
        }
```

2. Create `templates/reverse_text.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Reverse Text - Move</title>
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Reverse Text</h1>
        
        {message_html}
        
        <form action="/reverse-text" method="post">
            <input type="hidden" name="action" value="reverse_text">
            
            <label for="input_text">Enter Text:</label>
            <input type="text" id="input_text" name="text" required>
            
            <button type="submit">Reverse</button>
        </form>
        
        <p><a href="/">Back to Home</a></p>
    </div>
</body>
</html>
```

3. Update `move-webserver.py`:
```python
from text_handler import reverse_text

# In MyServer class:
def do_GET(self):
    # ... existing routes ...
    elif self.path == "/reverse-text":
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(os.path.join("templates", "reverse_text.html"), "r") as f:
            html_content = f.read().replace("{message_html}", "")
            self.wfile.write(bytes(html_content, "utf-8"))

def do_POST(self):
    # ... existing code ...
    elif action == "reverse_text" and self.path == "/reverse-text":
        try:
            text = form.getvalue('text')
            if not text:
                message = "No text provided"
                message_type = "error"
                self.respond_with_form(self.path, message, message_type)
                return
                
            result = reverse_text(text)
            
            if result['success']:
                message = f"{result['message']}: {result['result']}"
                message_type = "success"
            else:
                message = result['message']
                message_type = "error"
                
            self.respond_with_form(self.path, message, message_type)
            
        except Exception as e:
            self.respond_with_form(self.path, f"Error: {str(e)}", "error")
```

## Conclusion

Following these guidelines will help maintain consistency and reliability when extending the Move webserver. Remember to:

- Keep feature logic in separate handler files
- Create clear and user-friendly templates
- Handle errors gracefully
- Test thoroughly before deployment
