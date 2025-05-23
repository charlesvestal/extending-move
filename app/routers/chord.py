"""
Chord router - handles chord kit generation functionality
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/chord", response_class=HTMLResponse)
async def get_chord_form(request: Request):
    """Get the chord generation form."""
    return templates.TemplateResponse(
        "components/chord.html",
        {"request": request}
    )

# Note: Chord processing is handled entirely client-side with JavaScript
# The existing chord.js handles all the complex audio processing
