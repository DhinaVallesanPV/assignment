# Financial Data PII Scrubber

## Overview
A secure application for scrubbing Personally Identifiable Information (PII) from financial statements. The system ensures that sensitive data is removed locally before any information is stored in a database or transmitted to AI services for analysis.

## Features
- **Multi-format Support**: Extracts text from PDF, DOCX, CSV, and TXT files.
- **Local PII Scrubbing**: Uses regex and pattern matching to replace PII with unique placeholders (e.g., `<PERSON_1>`, `<ACCOUNT_1>`).
- **Secure Persistence**: Only scrubbed text is stored in PostgreSQL.
- **AI-Powered Analysis**: Integration with Groq for generating financial summaries and grounded chat based on scrubbed data.
- **Web Interface**: Intuitive UI for uploading files, viewing scrubbed output, and interacting with AI.

## Architecture
- **Frontend**: HTML/CSS/JS (Vanilla)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **AI Service**: Groq API (Llama-3 models)
- **Scrubbing Pipeline**: Custom local processing logic ensuring zero raw data leakage to external APIs.

## Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Groq API Key

## Setup & Installation

### 1. Database Setup
Run the provided SQL scripts to initialize the database:
```bash
psql -U your_user -d your_db -f sql/schema.sql
psql -U your_user -d your_db -f sql/init_db.sql
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
GROQ_API_KEY=your_groq_api_key_here
MAX_FILES=20
MAX_UPLOAD_MB=25
```

### 3. Installation
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Startup
```bash
uvicorn app.main:app --reload
```
The application will be available at `http://localhost:8000`.

## API Usage
- `POST /api/scrub`: Upload files to be scrubbed. Returns a `Document` object with scrubbed text.
- `POST /api/documents/{id}/analysis`: Generates a structured financial analysis of the scrubbed document.
- `POST /api/chat`: Grounded chat interaction based on the scrubbed document content.
- `GET /health`: Checks database connectivity.

## Privacy Safeguards
1. **Zero-Raw-Persistence**: Raw files are processed in a temporary directory and deleted immediately after scrubbing.
2. **Local Scrubbing**: The PII scrubbing occurs entirely on the server side before database insertion.
3. **AI Isolation**: Only the `combined_scrubbed_text` is sent to Groq. No raw PII ever leaves the local environment.
4. **Safe Placeholders**: Placeholders preserve the structure and relationships of the data without revealing identity.
