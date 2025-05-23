"""
Restore router - handles Move Set restoration functionality
"""
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
import tempfile

from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/restore", response_class=HTMLResponse)
async def get_restore_form(request: Request):
    """Get the restore form with available Move Sets."""
    try:
        msets = list_msets()
        options_html = ""
        for mset in msets:
            options_html += f'<option value="{mset["id"]}">{mset["name"]} (ID: {mset["id"]})</option>'
        
        return templates.TemplateResponse(
            "components/restore.html",
            {
                "request": request,
                "options": options_html
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "components/restore.html",
            {
                "request": request,
                "message": f"Error loading Move Sets: {str(e)}",
                "message_type": "error",
                "options": ""
            }
        )

@router.post("/restore", response_class=HTMLResponse)
async def process_restore(
    request: Request,
    action: str = Form(...),
    file: UploadFile = File(...),
    mset_index: str = Form(...),
    mset_restorecolor: str = Form(...)
):
    """Process Move Set restoration."""
    if action != "restore":
        return templates.TemplateResponse(
            "components/restore.html",
            {
                "request": request,
                "message": "Invalid action",
                "message_type": "error",
                "options": ""
            }
        )
    
    # Create temporary file for upload
    temp_file = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ablbundle") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process the restoration
        success, message = restore_ablbundle(temp_file_path, mset_index, mset_restorecolor)
        message_type = "success" if success else "error"
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        # Reload Move Sets for the form
        msets = list_msets()
        options_html = ""
        for mset in msets:
            selected = 'selected' if str(mset["id"]) == mset_index else ''
            options_html += f'<option value="{mset["id"]}" {selected}>{mset["name"]} (ID: {mset["id"]})</option>'
        
        return templates.TemplateResponse(
            "components/restore.html",
            {
                "request": request,
                "message": message,
                "message_type": message_type,
                "options": options_html
            }
        )
    except Exception as e:
        # Clean up temporary file if it exists
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        
        # Reload Move Sets for error response
        try:
            msets = list_msets()
            options_html = ""
            for mset in msets:
                options_html += f'<option value="{mset["id"]}">{mset["name"]} (ID: {mset["id"]})</option>'
        except:
            options_html = ""
        
        return templates.TemplateResponse(
            "components/restore.html",
            {
                "request": request,
                "message": f"Error restoring bundle: {str(e)}",
                "message_type": "error",
                "options": options_html
            }
        )
