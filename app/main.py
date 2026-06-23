import os
import io
import json
import logging
from typing import List
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
class Settings(BaseSettings):
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_model: str = Field("google/gemini-2.0-flash-lite-preview-02-05:free", env="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    debug: bool = Field(False, env="DEBUG")
    max_file_size: int = Field(10 * 1024 * 1024)  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Load settings - will raise error if OPENROUTER_API_KEY is missing
settings = Settings()
logger.info(f"Settings loaded. Using model: {settings.openrouter_model}")

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
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Medical Billing Auditor"
        }
    
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

# Initialize OpenRouter client (will fail if no API key)
openrouter_client = OpenRouterClient(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url
)
logger.info("OpenRouter client initialized successfully")

# --- PDF Parser ---
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF using PyPDF.
    """
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages")
        
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        
        if not extracted_text.strip():
            raise ValueError("No text could be extracted from the PDF")
        
        logger.info(f"Extracted {len(extracted_text)} characters from PDF")
        return extracted_text
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

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
            import re
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

# --- Routes ---

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
        "debug": settings.debug
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
        
        # Extract text from PDF
        raw_text = extract_text_from_pdf(contents)
        logger.info(f"Extracted {len(raw_text)} characters of text")
        
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

# --- Run ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

    