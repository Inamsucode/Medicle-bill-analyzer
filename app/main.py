import os
import io
import logging
from typing import List, Optional
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader
from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

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
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    debug: bool = Field(False, env="DEBUG")
    max_file_size: int = Field(10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: List[str] = Field([".pdf"], env="ALLOWED_EXTENSIONS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Load settings
try:
    settings = Settings()
    logger.info("Settings loaded successfully")
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    # Fallback to environment variables directly
    settings = Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )

# --- Data Contracts (Pydantic Models) ---
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
    description="AI-powered medical billing audit and dispute letter generator",
    version="1.0.0",
    debug=settings.debug
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.openai_api_key)

# --- PDF Parsing Service ---
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF file bytes using PyPDF.
    
    Args:
        file_bytes: Raw PDF file bytes
        
    Returns:
        Extracted text as string
        
    Raises:
        ValueError: If PDF is corrupted or empty
    """
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages")
        
        extracted_text = ""
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
            else:
                logger.warning(f"No text extracted from page {page_num}")
        
        if not extracted_text.strip():
            raise ValueError("No text could be extracted from the PDF")
        
        logger.info(f"Extracted {len(extracted_text)} characters from PDF")
        return extracted_text
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

# --- OpenAI Analysis Service ---
def analyze_billing_text(text: str) -> AuditResponse:
    """
    Analyze medical billing text using OpenAI with structured output.
    
    Args:
        text: Extracted text from medical bill
        
    Returns:
        AuditResponse with analysis results
        
    Raises:
        Exception: If OpenAI API call fails
    """
    try:
        system_instruction = (
            "You are an expert medical billing auditor with 20+ years of experience in "
            "US healthcare billing, CPT coding, and regulatory compliance. Your task is to:\n\n"
            "1. **Identify** all CPT/medical codes mentioned in the bill\n"
            "2. **Audit** each code for:\n"
            "   - Upcoding (billing for a more expensive service than provided)\n"
            "   - Setting mismatches (e.g., charging ICU rates for outpatient care)\n"
            "   - Unbundling (billing separately for services that should be combined)\n"
            "   - Duplicate charges\n"
            "   - Medicare/insurance rate violations\n"
            "3. **Calculate** the total potential savings by identifying overcharges\n"
            "4. **Generate** a professional, persuasive dispute letter addressed to the "
            "billing department with specific citations and requests for adjustment\n\n"
            "Be thorough, specific, and professional in your analysis."
        )

        user_prompt = f"Analyze this medical bill text and provide a complete audit:\n\n{text}"

        logger.info("Sending request to OpenAI API...")
        
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            response_format=AuditResponse,
            temperature=0.3,  # Lower temperature for more consistent results
        )

        result = completion.choices[0].message.parsed
        logger.info(f"OpenAI analysis complete. Found {len(result.flagged_codes)} codes, ${result.total_savings} in savings")
        
        return result

    except Exception as e:
        logger.error(f"OpenAI analysis failed: {str(e)}")
        raise Exception(f"AI analysis failed: {str(e)}")

# --- Alternative: Mock Analysis for Testing ---
def analyze_billing_text_mock(text: str) -> AuditResponse:
    """
    Mock analysis function for testing without OpenAI API.
    """
    logger.info("Using mock analysis (OpenAI API not configured)")
    return AuditResponse(
        total_savings=4500,
        flagged_codes=[
            FlaggedCode(
                code="99291",
                description="Critical Care Service (First Hour)",
                status="flagged",
                reason="Setting mismatch. Patient record indicates treatment was administered in an outpatient clinic, not an ICU environment. Should be down-tiered to standard outpatient evaluation."
            ),
            FlaggedCode(
                code="99214",
                description="Office/Outpatient Visit (Detailed)",
                status="valid",
                reason="Correct alignment with clinical documentation. Rate matches Medicare guidelines for this setting."
            ),
            FlaggedCode(
                code="93000",
                description="Electrocardiogram (EKG)",
                status="flagged",
                reason="Unbundled charge. EKG is typically included in the hospital stay and should not be billed separately."
            )
        ],
        letter="""Dear Billing Department,

I am writing to formally dispute charges on my recent medical statement (Account #: 2024-001) dated January 15, 2024.

I have identified the following billing discrepancies:

1. CPT Code 99291 (Critical Care Service): This code was applied in error. The service was provided in an outpatient clinic setting, not a critical care environment. I request this be recoded to an appropriate outpatient visit code.

2. CPT Code 93000 (Electrocardiogram): This service appears to be unbundled from the hospital stay and should be included in the facility charges.

Total overcharge identified: $4,500

Please review these items and provide a corrected statement within 30 days. I look forward to your prompt resolution of this matter.

Sincerely,
[Patient Name]
[Patient ID]"""
    )

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
        "openai_configured": bool(settings.openai_api_key),
        "debug": settings.debug
    }

@app.post("/api/analysis/upload", response_class=HTMLResponse)
async def handle_upload(request: Request, file: UploadFile = File(...)):
    """
    Process uploaded PDF and return analysis results.
    
    This endpoint:
    1. Validates the uploaded file
    2. Extracts text from the PDF
    3. Analyzes the text using OpenAI
    4. Returns rendered HTML component for HTMX
    """
    try:
        # --- File Validation ---
        if not file.filename:
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": "No file selected"}
            )
        
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.allowed_extensions:
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": f"Only {', '.join(settings.allowed_extensions)} files are allowed"}
            )
        
        # Read file contents
        contents = await file.read()
        
        # Check file size
        if len(contents) > settings.max_file_size:
            return templates.TemplateResponse(
                "components/error.html",
                {"request": request, "error": f"File too large. Maximum size is {settings.max_file_size // (1024*1024)}MB"}
            )
        
        logger.info(f"Processing file: {file.filename} ({len(contents)} bytes)")
        
        # --- Process the file ---
        # Extract text from PDF
        raw_text = extract_text_from_pdf(contents)
        logger.info(f"Extracted {len(raw_text)} characters of text")
        
        # Analyze with OpenAI (or use mock if no API key)
        if settings.openai_api_key:
            analysis_results = analyze_billing_text(raw_text)
        else:
            logger.warning("No OpenAI API key found - using mock analysis")
            analysis_results = analyze_billing_text_mock(raw_text)
        
        # --- Return HTML Fragment ---
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
            {"request": request, "error": "An unexpected error occurred. Please try again."}
        )

# --- Optional: Background Task Support ---
from fastapi import BackgroundTasks

@app.post("/api/analysis/upload-async", response_class=HTMLResponse)
async def handle_upload_async(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Process uploaded PDF asynchronously with background task.
    Useful for large files or complex analysis.
    """
    # Store file temporarily
    contents = await file.read()
    temp_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)
    
    with open(temp_path, "wb") as f:
        f.write(contents)
    
    # Start background task
    background_tasks.add_task(
        process_file_background,
        temp_path,
        request
    )
    
    return templates.TemplateResponse(
        "components/processing.html",
        {"request": request, "message": "Processing your file in the background..."}
    )

async def process_file_background(file_path: str, request: Request):
    """Background task for file processing."""
    try:
        # Read file
        with open(file_path, "rb") as f:
            contents = f.read()
        
        # Process
        raw_text = extract_text_from_pdf(contents)
        if settings.openai_api_key:
            analysis = analyze_billing_text(raw_text)
        else:
            analysis = analyze_billing_text_mock(raw_text)
        
        # TODO: Store results in database
        logger.info(f"Background processing complete for {file_path}")
        
    except Exception as e:
        logger.error(f"Background processing failed: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Error Handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "components/error.html",
        {"request": request, "error": exc.detail},
        status_code=exc.status_code
    )

# --- Run with: uvicorn app.main:app --reload ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

