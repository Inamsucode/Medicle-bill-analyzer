from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.services.agent import run_audit

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/run", response_class=HTMLResponse)
async def run_analysis(request: Request):
    audit_html, letter_html = run_audit()
    return HTMLResponse(content=f"{audit_html}{letter_html}")
