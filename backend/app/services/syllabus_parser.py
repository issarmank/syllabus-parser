# app/services/syllabus_parser.py
import json, re
from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.models import Event, ParseResult
from .pdf_reader import extract_text_from_pdf

SYSTEM = (
    "You analyze university course syllabus text. "
    "Return ONLY valid JSON with this shape:\n"
    '{"summary":"<concise 2-4 sentence overview>",'
    '"events":[{"title":"<event>","date":"YYYY-MM-DD"}]}\n'
    "Include only dated academic deadlines (exams, assignments, projects, quizzes, major due dates). "
    "Skip undated items."
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def heuristic(text: str) -> ParseResult:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    summary = " ".join(lines[:5])[:400]
    events: list[Event] = []
    for l in lines:
        low = l.lower()
        if any(k in low for k in ("exam","midterm","final","quiz","assignment","project","due")):
            events.append(Event(title=l[:120], date=""))
        if len(events) >= 12:
            break
    return ParseResult(summary=summary, events=events)

def parse_pdf_bytes(data: bytes, max_pages: int = 12) -> ParseResult:
    text = extract_text_from_pdf(data, max_pages=max_pages)
    if not OPENAI_API_KEY:
        return heuristic(text)

    client = OpenAI(api_key=OPENAI_API_KEY)
    truncated = text[:30000]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": truncated},
        ],
    )
    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
        summary = (data.get("summary") or "").strip()
        events_out: list[Event] = []
        for e in data.get("events", []):
            title = (e.get("title") or "").strip()
            date = (e.get("date") or "").strip()
            if date and not DATE_RE.match(date):
                continue
            if title:
                events_out.append(Event(title=title, date=date))
        return ParseResult(summary=summary, events=events_out)
    except Exception:
        return heuristic(text)
