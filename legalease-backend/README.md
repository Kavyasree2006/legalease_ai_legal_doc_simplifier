# LegalEase Backend

FastAPI backend for the LegalEase AI-Powered Legal Document Simplifier and Risk Analyzer.

## Architecture

React/Tailwind → FastAPI → PDF/DOCX extraction + Tesseract OCR → spaCy/NLTK → Ollama/Gemma 3 → PostgreSQL → ReportLab PDF

Supabase is intentionally not required in this version. PostgreSQL is accessed through SQLAlchemy, so Supabase Postgres can be introduced later by changing `DATABASE_URL`.

## 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+ OR Docker
- Tesseract OCR installed and available on PATH for scanned PDFs
- Ollama installed and running locally
- A Gemma 3 model pulled into Ollama

Example Ollama setup:

```bash
ollama serve
ollama pull gemma3:4b
```

If you use another Gemma 3 tag, change `OLLAMA_MODEL` in `.env`.

## 2. Start PostgreSQL

Using Docker:

```bash
docker compose up -d postgres
```

## 3. Python environment

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set a strong `SECRET_KEY`.

## 4. Start API

```bash
uvicorn app.main:app --reload --port 8000
```

API docs:

- http://localhost:8000/docs
- http://localhost:8000/health

## 5. Frontend

Set the frontend `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Then run the React app with `npm run dev`.

## API contract

### Authentication
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Documents
- `GET /api/documents`
- `GET /api/documents/{id}`
- `POST /api/documents/upload`
- `DELETE /api/documents/{id}`

### Analysis
- `GET /api/analysis/{id}`
- `GET /api/analysis/document/{document_id}`
- `POST /api/analysis/analyze`

### History
- `GET /api/history`

### Reports
- `GET /api/reports/{document_id}/download`

### Settings
- `GET /api/settings`
- `PATCH /api/settings`

## Real analysis flow

1. Authenticated user uploads PDF/DOCX.
2. Backend validates extension and 25 MB limit.
3. PDF/DOCX text is extracted.
4. If a PDF has no selectable text, Tesseract OCR is attempted.
5. Extracted text is stored in PostgreSQL.
6. A pending Analysis record is created.
7. FastAPI background processing calls Ollama/Gemma 3.
8. The LLM returns summary, simplified text, risk clauses and risk score as JSON.
9. spaCy/NLTK-based processing contributes document complexity calculation.
10. Results and risk clauses are stored in PostgreSQL.
11. React polls the analysis endpoint until completion.
12. ReportLab generates a real PDF when requested.

## No dummy data

The backend does not seed example users, documents, risks or analysis results. A document only appears after a real authenticated upload. If Ollama fails, the analysis is marked `failed` and the API returns the error instead of fabricating an analysis.

## Security notes

- Passwords are hashed with Argon2.
- API routes require a signed JWT except health/root endpoints.
- Users can only access their own documents and reports.
- File type and size are validated.
- Never put a Supabase service-role/secret key into the React `.env`.
- Before production, add token revocation/rotation, rate limiting, HTTPS, malware scanning and object-storage isolation.

## Supabase later

When you are ready for Supabase, the simplest migration is to point SQLAlchemy at the Supabase Postgres connection string:

```env
DATABASE_URL=postgresql+psycopg://...
```

If you later want Supabase Auth/Storage as well, the auth/storage services can be swapped independently without changing the frontend API contract.
