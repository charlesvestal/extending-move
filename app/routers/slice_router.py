"""
Slice router - handles audio slicing functionality
"""
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
import os
import tempfile
import json

from handlers.slice_handler_class import SliceHandler

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/slice", response_class=HTMLResponse)
async def get_slice_form(request: Request):
    """Get the slice form."""
    return templates.TemplateResponse(
        "components/slice.html",
        {"request": request}
    )

@router.post("/slice")
async def process_slice(
    request: Request,
    action: str = Form(...),
    file: UploadFile = File(...),
    kit_type: str = Form("choke"),
    num_slices: int = Form(16),
    mode: str = Form("download"),
    regions: str = Form(None)
):
    """Process audio slicing."""
    if action != "slice":
        return templates.TemplateResponse(
            "components/slice.html",
            {
                "request": request,
                "message": "Invalid action",
                "message_type": "error"
            }
        )
    
    # Create a mock form object that matches the existing handler expectations
    class MockForm:
        def __init__(self, **kwargs):
            self._values = kwargs
            self._files = {}
        
        def getvalue(self, key, default=None):
            return self._values.get(key, default)
        
        def __contains__(self, key):
            return key in self._values or key in self._files
        
        def __getitem__(self, key):
            if key in self._files:
                return self._files[key]
            return self._values[key]
    
    # Create temporary file for upload
    temp_file = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Create mock file field
        class MockFileField:
            def __init__(self, filename, filepath):
                self.filename = filename
                self.filepath = filepath
                self.file = open(filepath, 'rb')
        
        # Create mock form
        form_data = {
            'action': action,
            'kit_type': kit_type,
            'num_slices': str(num_slices),
            'mode': mode
        }
        
        if regions:
            form_data['regions'] = regions
        
        mock_form = MockForm(**form_data)
        mock_form._files['file'] = MockFileField(file.filename, temp_file_path)
        
        # Use existing slice handler
        slice_handler = SliceHandler()
        
        # Handle download response
        def response_handler(status, headers, content):
            # Create FastAPI response
            response = Response(content=content, status_code=status)
            for header_name, header_value in headers:
                response.headers[header_name] = header_value
            return response
        
        result = slice_handler.handle_post(mock_form, response_handler)
        
        # Clean up
        if hasattr(mock_form._files['file'], 'file'):
            mock_form._files['file'].file.close()
        os.unlink(temp_file_path)
        
        # If result is None, the response was already sent
        if result is None:
            return response_handler(200, [], b"")
        
        # If result contains download info, handle file download
        if result.get('download'):
            bundle_path = result.get('bundle_path')
            if bundle_path and os.path.exists(bundle_path):
                with open(bundle_path, 'rb') as f:
                    content = f.read()
                os.remove(bundle_path)
                
                return Response(
                    content=content,
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={os.path.basename(bundle_path)}"
                    }
                )
        
        # Regular template response
        message_type = "success" if result.get('success') else "error"
        return templates.TemplateResponse(
            "components/slice.html",
            {
                "request": request,
                "message": result.get('message', ''),
                "message_type": message_type
            }
        )
        
    except Exception as e:
        # Clean up temporary file if it exists
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        
        return templates.TemplateResponse(
            "components/slice.html",
            {
                "request": request,
                "message": f"Error processing slice: {str(e)}",
                "message_type": "error"
            }
        )
