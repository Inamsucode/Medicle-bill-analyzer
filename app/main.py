import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# FORCE LOAD .env FROM PROJECT ROOT - ABSOLUTE PATH
# ============================================================

# Get the absolute path to the project root (where main.py is located)
# This works regardless of where you run the script from
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.absolute()
env_file = project_root / ".env"

print("=" * 60)
print("FORCE LOADING .env FILE")
print("=" * 60)
print(f"Script directory: {script_dir}")
print(f"Project root: {project_root}")
print(f"Looking for .env at: {env_file}")
print(f".env exists: {env_file.exists()}")

# FORCE LOAD: Try multiple methods to load .env
env_loaded = False

# Method 1: Load from absolute path
if env_file.exists():
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f".env content preview: {content[:50]}...")
        
        load_dotenv(dotenv_path=str(env_file), override=True)
        print(f"✅ Method 1: .env loaded from: {env_file}")
        env_loaded = True
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")

# Method 2: Try loading from current directory
if not env_loaded:
    try:
        load_dotenv(override=True)
        if os.getenv("OPENROUTER_API_KEY"):
            print(f"✅ Method 2: .env loaded from current directory: {os.getcwd()}")
            env_loaded = True
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")

# Method 3: Try loading with explicit encoding
if not env_loaded and env_file.exists():
    try:
        with open(env_file, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
                    print(f"✅ Set {key}={value[:15]}...")
        env_loaded = True
        print("✅ Method 3: .env loaded manually")
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")

# Verify API key is loaded
API_KEY = os.getenv("OPENROUTER_API_KEY")

print("-" * 60)
if API_KEY:
    print(f"✅ API Key loaded: {API_KEY[:15]}...")
else:
    print("❌ API Key NOT loaded!")
    print("\nPlease create .env file with:")
    print("OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here")
    print("OPENROUTER_MODEL=openrouter/free")
    print("OPENROUTER_BASE_URL=https://openrouter.ai/api/v1")
    print("DEBUG=true")
    print("\nOR create config.py file with:")
    print("API_KEY = 'sk-or-v1-your-actual-key-here'")
    print("=" * 60)
    raise ValueError("OPENROUTER_API_KEY not found in .env file")

print("=" * 60)

# ============================================================
# REST OF IMPORTS
# ============================================================

import io
import json
import re
import logging
from typing import List
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import httpx

# Try importing OCR libraries (optional - fail gracefully if not installed)
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
    logger_ocr = logging.getLogger(__name__)
    logger_ocr.info("OCR libraries loaded successfully")
except ImportError as e:
    OCR_AVAILABLE = False
    print(f"OCR libraries not available: {e}. Scanned PDFs will not work.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
class Settings(BaseSettings):
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_model: str = Field("openrouter/free", env="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    debug: bool = Field(False, env="DEBUG")
    max_file_size: int = Field(10 * 1024 * 1024)  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Load settings - will use the .env we already loaded
try:
    settings = Settings()
    logger.info(f"Settings loaded. Using model: {settings.openrouter_model}")
    print(f"✅ Settings loaded successfully")
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    raise

# --- Data Models ---
class FlaggedCode(BaseModel):
    code: str = Field(..., description="CPT or billing code")
    description: str = Field(..., description="Description of the service")
    status: str = Field(..., description="Must be 'flagged' or 'valid'")
    reason: str = Field(..., description="Explanation of why this code was flagged or validated")

class AuditResponse(BaseModel):
    total_savings: int = Field(..., description="Total potential savings in dollars")
    flagged_codes: List[FlaggedCode] = Field(..., description="List of analyzed codes")
    letter: str = Field(..., description="Generated dispute letter")

# --- Initialize FastAPI ---
app = FastAPI(
    title="Medical Billing Auditor",
    description="AI-powered medical billing audit using OpenRouter",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# --- OpenRouter Client ---
class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Medical Billing Auditor"
        }
        print(f"✅ OpenRouter client initialized with key: {api_key[:15]}...")
    
    async def chat_completion(self, model: str, messages: List[dict]) -> dict:
        """
        Send a chat completion request to OpenRouter.
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter API error: {e.response.text}")
                raise Exception(f"OpenRouter API error: {e.response.text}")
            except Exception as e:
                logger.error(f"OpenRouter request failed: {str(e)}")
                raise

# Initialize OpenRouter client
openrouter_client = OpenRouterClient(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url
)
logger.info("OpenRouter client initialized successfully")

# --- Enhanced PDF Parser with OCR Support ---

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF using PyPDF with better error handling.
    Attempts multiple extraction methods.
    """
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages")
        
        extracted_text = ""
        extraction_methods_used = []
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                # Method 1: Standard text extraction
                text = page.extract_text()
                if text and text.strip():
                    extracted_text += text + "\n"
                    if "standard" not in extraction_methods_used:
                        extraction_methods_used.append("standard")
                else:
                    # Method 2: Try layout extraction mode (better for complex layouts)
                    try:
                        text = page.extract_text(extraction_mode="layout")
                        if text and text.strip():
                            extracted_text += text + "\n"
                            if "layout" not in extraction_methods_used:
                                extraction_methods_used.append("layout")
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Error extracting page {page_num}: {str(e)}")
                continue
        
        if extracted_text.strip():
            logger.info(f"Extracted {len(extracted_text)} characters from PDF using methods: {', '.join(extraction_methods_used)}")
            return extracted_text
        else:
            # No text extracted - try OCR if available
            if OCR_AVAILABLE:
                logger.info("No text extracted with standard methods. Attempting OCR...")
                return extract_text_with_ocr(file_bytes)
            else:
                raise ValueError("No text could be extracted from the PDF. The file may be scanned or image-based. Install pytesseract and pdf2image for OCR support.")
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_text_with_ocr(file_bytes: bytes) -> str:
    """
    Extract text from scanned PDF using OCR.
    Requires pytesseract and pdf2image to be installed.
    """
    if not OCR_AVAILABLE:
        raise ValueError("OCR libraries (pytesseract, pdf2image) are not installed. Please install them for scanned PDF support.")
    
    try:
        logger.info("Starting OCR extraction...")
        
        # Convert PDF to images
        images = convert_from_bytes(file_bytes)
        extracted_text = ""
        
        for i, image in enumerate(images):
            logger.info(f"Performing OCR on page {i+1} of {len(images)}...")
            # Perform OCR on each image
            text = pytesseract.image_to_string(image)
            if text.strip():
                extracted_text += f"Page {i+1}:\n{text}\n\n"
        
        if not extracted_text.strip():
            raise ValueError("OCR could not extract any text from the scanned PDF.")
        
        logger.info(f"OCR extraction successful: {len(extracted_text)} characters extracted from {len(images)} pages")
        return extracted_text
        
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        raise ValueError(f"OCR extraction failed: {str(e)}")

# --- OpenRouter Analysis ---
async def analyze_with_openrouter(text: str) -> AuditResponse:
    """
    Analyze medical billing text using OpenRouter with structured output.
    """
    system_instruction = """You are an expert medical billing auditor with 20+ years of experience in US healthcare billing, CPT coding, and regulatory compliance.

Your task is to analyze the provided medical bill and return a JSON response with this EXACT structure:

{
    "total_savings": integer (total potential savings in dollars),
    "flagged_codes": [
        {
            "code": "CPT code as string",
            "description": "Description of the service",
            "status": "flagged" or "valid",
            "reason": "Detailed explanation of why this code was flagged or validated"
        }
    ],
    "letter": "Professional dispute letter as a string"
}

Analyze the bill for:
1. Upcoding (billing for a more expensive service than provided)
2. Setting mismatches (ICU rates for outpatient care)
3. Unbundling (billing separately for services that should be combined)
4. Duplicate charges
5. Medicare/insurance rate violations

Be thorough and specific. The letter should be professional and persuasive."""

    user_prompt = f"Analyze this medical bill text and provide a complete audit:\n\n{text}"

    logger.info(f"Sending request to OpenRouter using model: {settings.openrouter_model}")

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]

    try:
        # Get response from OpenRouter
        response = await openrouter_client.chat_completion(
            model=settings.openrouter_model,
            messages=messages
        )
        
        # Extract content from response
        content = response["choices"][0]["message"]["content"]
        logger.info(f"OpenRouter response received: {len(content)} characters")
        
        # Parse JSON response
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                data = json.loads(content)
            
            # Validate and convert to AuditResponse
            return AuditResponse(
                total_savings=data.get("total_savings", 0),
                flagged_codes=[
                    FlaggedCode(
                        code=c.get("code", ""),
                        description=c.get("description", ""),
                        status=c.get("status", "valid"),
                        reason=c.get("reason", "")
                    )
                    for c in data.get("flagged_codes", [])
                ],
                letter=data.get("letter", "No dispute letter generated.")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {content[:500]}...")
            
            # Return error response
            raise Exception(f"Failed to parse AI response as JSON. Response: {content[:200]}...")
            
    except Exception as e:
        logger.error(f"OpenRouter analysis failed: {str(e)}")
        raise Exception(f"AI analysis failed: {str(e)}")

# ============================================================
# ALL ROUTES
# ============================================================

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check if environment variables are loading."""
    return {
        "openrouter_api_key_exists": bool(settings.openrouter_api_key),
        "openrouter_api_key_preview": settings.openrouter_api_key[:15] + "..." if settings.openrouter_api_key else "MISSING",
        "openrouter_model": settings.openrouter_model,
        "openrouter_base_url": settings.openrouter_base_url,
        "debug": settings.debug,
        "ocr_available": OCR_AVAILABLE
    }

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": settings.openrouter_model,
        "debug": settings.debug,
        "ocr_available": OCR_AVAILABLE
    }

@app.post("/api/analysis/upload", response_class=HTMLResponse)
async def handle_upload(request: Request, file: UploadFile = File(...)):
    """
    Process uploaded PDF and return analysis results using OpenRouter.
    """
    try:
        # --- File Validation ---
        if not file.filename:
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": "No file selected"}
            )
        
        # Check file extension
        if not file.filename.lower().endswith('.pdf'):
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": "Only PDF files are allowed"}
            )
        
        # Read file
        contents = await file.read()
        
        # Check file size
        if len(contents) > settings.max_file_size:
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": f"File too large. Maximum size is {settings.max_file_size // (1024*1024)}MB"}
            )
        
        logger.info(f"Processing file: {file.filename} ({len(contents)} bytes)")
        
        # Extract text from PDF with enhanced extraction and OCR fallback
        try:
            raw_text = extract_text_from_pdf(contents)
            logger.info(f"Extracted {len(raw_text)} characters of text")
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": f"Could not extract text from PDF: {str(e)}"}
            )
        
        # Check if we got enough text
        if len(raw_text.strip()) < 50:
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": "Not enough text could be extracted from the PDF. Please ensure the PDF contains readable text."}
            )
        
        # Analyze with OpenRouter
        analysis_results = await analyze_with_openrouter(raw_text)
        
        # Return HTML fragment
        return templates.TemplateResponse(
            "components/audit_results.html",
            {
                "request": request,
                "savings": analysis_results.total_savings,
                "codes": analysis_results.flagged_codes,
                "letter": analysis_results.letter
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return templates.TemplateResponse(
            "components/error.html",
            {"request": request, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {"request": request, "error": f"An error occurred: {str(e)}"}
        )

# ============================================================
# RUN - This MUST be at the VERY END of the file
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )