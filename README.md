# Medical Billing Auditor

A server-side FastAPI application for medical billing auditing with Jinja2 templates and HTMX-driven UI updates.

## Project structure

- `app/main.py`: FastAPI initialization, static asset mounting, template rendering
- `app/api/endpoints`: server routes returning HTML fragments
- `app/core/config.py`: environment variable parsing
- `app/services`: PDF parsing, AI audit agent, and Greptile integration
- `app/static`: compiled Tailwind CSS and optional JavaScript
- `app/templates`: Jinja2 views and dynamic UI components

## Setup

1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. `copy .env.example .env`
5. `uvicorn app.main:app --reload`

## Notes

- HTMX is included in `base.html` for dynamic partial updates.
- Add real PDF parsing and AI logic in `app/services`.
