# Syllabus Parser

Upload a syllabus PDF to automatically extract course information for students success

## Tech Stack
- Frontend: React + Vite (TypeScript), utility CSS classes, Fetch API
- Backend: FastAPI (Python), Uvicorn, Pydantic
- AI: OpenAI Chat Completions (structured JSON extraction) with heuristic fallback
- PDF: Text extraction via a PDF reader utility
- Export: Client-side ICS (iCalendar) and CSV generation

## What It Does (Features)
- PDF upload: Sends the syllabus to the backend for parsing
- Summary: Concise 2–4 sentence overview
- Events:
  - Extracts academic deadlines with ISO dates (YYYY-MM-DD)
  - Displays in a friendly format (“September 23rd, 2025”)
  - Export:
    - .ics for Google/Apple Calendar (all-day events)
    - .csv for Notion (Title, Date)
- Evaluations:
  - Extracts assessment components and their weights
  - Normalizes weights so total ≈ 100%
  - Renders a table with a computed total row and subtle warning if not exactly 100

## How It Works (Flow)
1. User uploads a PDF in the frontend.
2. Backend extracts text (limits pages/characters for speed).
3. If OpenAI API key is set:
   - Sends text with strict JSON instructions to the model.
   - Parses summary, events, and evaluations from JSON.
4. If the model fails or no key:
   - Heuristic fallback scans lines for dates, exam/assignment keywords, and percent weights.
5. Evaluations are validated and normalized to sum to 100.
6. Frontend renders sections and offers export buttons for calendars/Notion.

## Key Files (Frontend)
- src/App.tsx
  - Uploads PDFs, calls backend, displays Summary, Events, Evaluations
  - Wires export buttons (ICS/CSV)
- src/components/EventDate.tsx
  - Formats ISO dates to “Month DayOrdinal, Year”
- src/components/EvaluationsTable.tsx
  - Renders assessment/weight table with total
- src/utils/types.ts
  - EventItem, EvaluationItem, ParseResult types
- src/utils/exportCalendar.ts
  - Builds ICS and CSV on the client
  - ICS details:
    - All-day events: DTSTART;VALUE=DATE:YYYYMMDD
    - DTEND is next day (exclusive)
    - Unique UID per event
  - CSV details:
    - Columns: Title, Date (ISO)

## Key Files (Backend)
- app/main.py
  - FastAPI app setup, middleware (e.g., CORS), route wiring
- app/services/syllabus_parser.py
  - System prompt, OpenAI call, heuristics, validation, normalization
- app/services/pdf_reader.py
  - Extracts text from PDFs (page/size limits)
- app/models.py
  - Pydantic models: Event, Assessment, ParseResult
- app/config.py
  - Loads OPENAI_API_KEY and other settings

## Setup
Backend (Python)
- macOS Terminal:
  - cd backend
  - python3 -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt
  - uvicorn app.main:app --reload

Frontend (Node)
- cd frontend
- npm install
- npm run dev

## Usage
1. Start backend and frontend.
2. Open the frontend URL (localhost:5173).
3. Upload a syllabus PDF.
4. Review Summary, Events, and Evaluation Breakdown.
5. Export:
   - Download .ics to import into Google/Apple Calendar
   - Download .csv to import into a Notion database (map Date column)

## Notes & Guarantees
- Event dates must be valid ISO; invalid dates are dropped.
- Evaluation weights are normalized to sum to ≈ 100 (largest item adjusted to fix rounding residue).
- ICS export creates all-day events for best compatibility.
- CSV export targets Notion import with minimal mapping.