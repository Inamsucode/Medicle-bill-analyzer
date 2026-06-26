#  Medical Bill Auditor

> AI-powered medical billing audit tool that identifies overcharges, coding errors, and generates professional dispute letters.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-AI-orange.svg)](https://openrouter.ai)
[![HTMX](https://img.shields.io/badge/HTMX-1.9.12-purple.svg)](https://htmx.org)
[![Tailwind](https://img.shields.io/badge/Tailwind-3.4.1-06B6D4.svg)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

##  Table of Contents

- [ Features](#-features)
- [ Tech Stack](#️-tech-stack)
- [ Quick Start](#-quick-start)
- [ Project Structure](#-project-structure)
- [ How It Works](#-how-it-works)
- [ API Key Setup](#-api-key-setup)
- [ AI Models](#-ai-models)
- [ Troubleshooting](#-troubleshooting)
- [ Screenshots](#-screenshots)
- [ Contributing](#-contributing)
- [ License](#-license)
- [ Contact](#-contact)

---

##  Features

### Core Features

| Feature | Description |
|---------|-------------|
|  **PDF Upload** | Drag-and-drop or click to upload medical bills |
|  **AI Analysis** | Identifies upcoding, setting mismatches, and unbundling |
|  **Savings Calculation** | Shows potential refund amount |
|  **Dispute Letters** | Generates professional appeal letters |
|  **Real-time Updates** | HTMX for seamless, no-refresh updates |
|  **Beautiful UI** | Glass-morphism design with dark theme |
|  **Secure** | API keys stored in `.env` (never exposed) |

### AI Audit Capabilities

The AI analyzes medical bills for:

| Audit Type | Description |
|------------|-------------|
| **Upcoding** | Billing for a more expensive service than provided |
| **Setting Mismatches** | Charging ICU rates for outpatient care |
| **Unbundling** | Billing separately for services that should be combined |
| **Duplicate Charges** | Multiple charges for the same service |
| **Rate Violations** | Charges exceeding Medicare/insurance rates |
| **CPT Code Validation** | Verifies correct CPT code usage |

---

##  Tech Stack

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Backend API framework |
| **HTMX** | Dynamic frontend updates |
| **Tailwind CSS** | Modern, responsive styling |
| **OpenRouter** | AI model access (free tier available) |
| **PyPDF** | PDF text extraction |
| **Jinja2** | Template rendering |
| **Pydantic** | Data validation |
| **Uvicorn** | ASGI server |

---

##  Quick Start

### Step 1: Get an OpenRouter API Key (FREE)

1. Go to [OpenRouter](https://openrouter.ai/keys)
2. Sign up (free, no credit card required)
3. Click **"Create Key"**
4. Copy your key (starts with `sk-or-v1-`)

### Step 2: Clone the Repository

```bash
git clone https://github.com/Inamsucode/Medicle-bill-analyzer.git
cd Medicle-bill-analyzer

# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# Replace YOUR_API_KEY_HERE with your actual key


# Create virtual environment (optional but recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # On Windows
# source .venv/bin/activate   # On Linux/Mac

# Install Python packages
pip install -r requirements.txt

# Install Tailwind CSS
npm install -D tailwindcss

# Build CSS
npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify


#To run the application
Set-Location 'C:\Users\Fariha Khalil\Medicle-bill-analyzer'; $env:OPENROUTER_API_KEY='placeholder'; py -m uvicorn app.main:app --reload




Step 6: Test the Application
Upload a PDF medical bill

Wait for AI analysis (15-30 seconds)

View results:

💰 Potential savings

📋 CPT code analysis

📝 Professional dispute letter

📁 Project Structure
text
Medicle-bill-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── api/                       # API endpoints
│   │   └── endpoints/             # Server routes returning HTML fragments
│   ├── core/
│   │   └── config.py             # Environment variable parsing
│   ├── services/                 # Business logic
│   │   ├── parser.py             # PDF parsing
│   │   └── agent.py              # AI audit agent
│   ├── templates/                # Jinja2 views
│   │   ├── base.html             # Base template
│   │   ├── index.html            # Main dashboard
│   │   └── components/           # Reusable UI components
│   │       ├── audit_results.html
│   │       ├── upload_zone.html
│   │       ├── savings_card.html
│   │       ├── dispute_letter.html
│   │       └── error.html
│   └── static/                   # Static assets
│       ├── css/
│       │   └── input.css         # Tailwind source
│       └── js/
│           └── main.js           # Client-side JavaScript
├── .env.example                   # Environment template
├── config.example.py              # Config template
├── requirements.txt              # Python dependencies
├── tailwind.config.js            # Tailwind CSS config
├── package.json                  # Node dependencies
├── .gitignore                    # Git ignore file
└── README.md                     # This file
🎯 How It Works
User Flow
text
┌─────────────────────────────────────────────────────────────┐
│                   1. User Uploads PDF                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Medical Bill PDF                                      │ │
│  │  - CPT Code 99214 - Office Visit: $500                 │ │
│  │  - CPT Code 99291 - Critical Care: $5,000              │ │
│  │  - Total: $5,500                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   2. AI Analysis                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  OpenRouter AI                                         │ │
│  │  - Analyze CPT codes                                   │ │
│  │  - Check for overcharges                               │ │
│  │  - Identify errors                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. Results Display                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  💰 Potential Savings: $4,500                          │ │
│  │  📋 CPT 99291 - Critical Care (Flagged)                │ │
│  │     Reason: Setting mismatch - Outpatient charged       │ │
│  │     at ICU rates                                       │ │
│  │  📝 Dispute Letter Generated                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
🔑 API Key Setup

Create .env in the project root:

env
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openrouter/free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Settings
DEBUG=true
MAX_FILE_SIZE=10485760


🤖 AI Models
Free Models (Recommended)
Model ID	Description	Quality
openrouter/free	Auto-routes to best free model	⭐⭐⭐⭐⭐
mistralai/mistral-7b-instruct:free	Mistral 7B	⭐⭐⭐⭐
meta-llama/llama-3.2-3b-instruct:free	Meta Llama 3.2	⭐⭐⭐⭐
google/gemini-flash-1.5:free	Google Gemini Flash	⭐⭐⭐⭐⭐
qwen/qwen-2.5-7b-instruct:free	Alibaba Qwen 2.5	⭐⭐⭐⭐

🐛 Troubleshooting
Common Errors and Solutions
❌ Error: "Missing Authentication header"
Solution:

bash
# Check if API key is set
cat .env  # Should show OPENROUTER_API_KEY=sk-or-v1-...

# Restart server
Set-Location 'C:\Users\Fariha Khalil\Medicle-bill-analyzer'; $env:OPENROUTER_API_KEY='placeholder'; py -m uvicorn app.main:app --reload
❌ Error: "Port 8000 already in use"
Solution:

bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID 12345 /F

# Or use different port
uvicorn app.main:app --reload --port 8001
❌ Error: "Could not extract text from PDF"
Solution:

bash
# Install OCR support
pip install pytesseract pdf2image

# For Windows, also install:
# Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# Poppler: https://github.com/oschwartz10612/poppler-windows/releases/
❌ Error: "ModuleNotFoundError: No module named 'config'"
Solution:

bash
# Create config.py from example
cp config.example.py config.py

# Or use .env file
cp .env.example .env
❌ Error: "UnicodeDecodeError" with .env
Solution:

bash
# Delete and recreate .env
del .env

# Create with correct encoding
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env
echo "OPENROUTER_MODEL=openrouter/free" >> .env
echo "OPENROUTER_BASE_URL=https://openrouter.ai/api/v1" >> .env
echo "DEBUG=true" >> .env
Quick Debug Checklist
.env file exists in project root

OPENROUTER_API_KEY is set correctly

Virtual environment is activated

All dependencies are installed

Server was restarted after changes

Visit /debug/env to check API key status

🔧 Development Commands
CSS Commands
bash
# Watch CSS changes (auto-rebuild)
npm run watch:css

# Build CSS for production
npm run build:css

# Or use npx directly
npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify
Server Commands
bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# With custom port
uvicorn app.main:app --reload --port 8080

# With debug logging
uvicorn app.main:app --reload --log-level debug
Testing Commands
bash
# Test API key loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENROUTER_API_KEY')[:15])"

# Test environment loading
python test_env.py



🤝 Contributing
Fork the repository

Create a feature branch:

bash
git checkout -b feature/amazing-feature
Commit your changes:

bash
git commit -m 'Add amazing feature'
Push to the branch:

bash
git push origin feature/amazing-feature
Open a Pull Request

Coding Standards
Python: PEP 8

HTML: Semantic HTML5

CSS: Tailwind utilities first

JavaScript: ES6+

📄 License
MIT License - Free for educational and commercial use.

📞 Contact
GitHub: @Inamsucode

Project Link: https://github.com/Inamsucode/Medicle-bill-analyzer

⭐ Show Your Support
If you found this project helpful, please give it a ⭐ on GitHub!

🙏 Acknowledgments
OpenRouter - Free AI models

FastAPI - Amazing Python framework

HTMX - Simple dynamic frontend

Tailwind CSS - Beautiful styling

PyPDF - PDF processing

📚 Resources
OpenRouter Documentation

FastAPI Documentation

HTMX Documentation

Tailwind CSS Documentation

Made with ❤️

Ready to audit your medical bills! 🏥💚

text

---


