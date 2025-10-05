# app/services/syllabus_parser.py
import json, re
import logging
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY
from app.models import Event, ParseResult, Assessment
from .pdf_reader import extract_text_from_pdf

SYSTEM = (
    "You analyze university course syllabus text. "
    "Return ONLY valid JSON with this shape:\n"
    '{"summary":"<concise 2-4 sentence overview>",'
    '"events":[{"title":"<event>","date":"YYYY-MM-DD"}],'
    '"evaluations":[{"name":"<assessment>","weight": <number 0-100>}]}'
    "\nRules:\n"
    "- events: only dated academic deadlines (exams, assignments, projects, quizzes, major due dates) with real dates in YYYY-MM-DD.\n"
    "- evaluations: list each graded assessment component (e.g., 'Assignments', 'Midterm Exam', 'Final Examination', 'Project').\n"
    "- weight is its percentage of the final grade (number). Do NOT include % sign.\n"
    "- If separate undergraduate / graduate columns exist, prefer the undergraduate column. One weight per assessment.\n"
    "- Ensure evaluation weights sum approximately to 100 (adjust proportionally if raw data slightly off)."
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

logger = logging.getLogger(__name__)

# Pydantic schema used for structured output from LangChain
class LcEvent(BaseModel):
    title: str = Field(..., description="Event title")
    date: Optional[str] = Field(None, description="YYYY-MM-DD date or empty if unknown")

class LcEvaluation(BaseModel):
    name: str
    weight: float

class LcSyllabus(BaseModel):
    summary: str
    events: list[LcEvent]
    evaluations: list[LcEvaluation]


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
    # Heuristic evaluations
    evals = _extract_evaluations(lines)
    return ParseResult(summary=summary, events=events, evaluations=evals)


def _extract_evaluations(lines: list[str]) -> list[Assessment]:
    import re
    rows: list[tuple[str,float]] = []
    pct_re = re.compile(r'(\d{1,3})\s*%')
    heading_hit = False
    for raw in lines:
        low = raw.lower()
        if any(h in low for h in ("evaluation", "assess", "grading", "weight")):
            heading_hit = True
        if not heading_hit:
            continue
        # Find percent values
        pcts = pct_re.findall(raw)
        if not pcts:
            continue
        # Name candidate: substring before first percent occurrence
        first_idx = raw.lower().find(pcts[0])
        name_part = raw[:first_idx].strip(" :-\t")
        # Clean name
        name_part = re.sub(r'\s+', ' ', name_part)
        if not name_part or len(name_part) < 2:
            continue
        # Skip column headers
        if any(x in name_part.lower() for x in ("undergraduate", "graduate", "tentative", "date")):
            continue
        # Take first % as weight (undergrad)
        weight_val = float(pcts[0])
        # Merge duplicates keeping highest
        existing = next((i for i,(n,_) in enumerate(rows) if n.lower()==name_part.lower()), None)
        if existing is not None:
            rows[existing] = (rows[existing][0], max(rows[existing][1], weight_val))
        else:
            rows.append((name_part, weight_val))
    if not rows:
        return []
    total = sum(w for _,w in rows)
    if total <= 0:
        return []
    # Normalize to 100
    normalized: list[Assessment] = []
    for name, w in rows:
        normalized.append(Assessment(name=name, weight=round((w/total)*100, 2)))
    # Minor rounding fix
    diff = round(100 - sum(a.weight for a in normalized), 2)
    if abs(diff) >= 0.05:
        # Adjust largest
        largest = max(normalized, key=lambda a: a.weight)
        largest.weight = round(largest.weight + diff, 2)
    return normalized


def _to_iso(date_str: str) -> Optional[str]:
    """Accept ISO (YYYY-MM-DD) or natural dates like 'September 23rd, 2025' and normalize to ISO.
    Returns None if parsing fails.
    """
    s = (date_str or "").strip()
    if not s:
        return None
    if DATE_RE.match(s):
        return s
    # remove ordinal suffixes (st, nd, rd, th)
    s = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", s, flags=re.IGNORECASE)
    # try common formats
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_pdf_bytes(pdf_bytes: bytes, max_pages: int = 12) -> ParseResult:
    text = extract_text_from_pdf(pdf_bytes, max_pages=max_pages)
    if not text.strip():
        return ParseResult(summary="No text extracted.", events=[], evaluations=[])
    if not OPENAI_API_KEY:
        return heuristic(text)

    try:
        # LangChain LLM with structured output
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system}"),
            ("user", "{text}")
        ])
        chain = prompt | llm.with_structured_output(LcSyllabus)
        result: LcSyllabus = chain.invoke({"text": text[:30000], "system": SYSTEM})

        summary = (result.summary or "").strip()

        # Events (normalize date to ISO when possible)
        events_out: list[Event] = []
        for e in result.events or []:
            title = (e.title or "").strip()
            date_raw = (e.date or "").strip()
            date_iso = _to_iso(date_raw) if date_raw else None
            if date_raw and not date_iso:
                continue
            if title:
                events_out.append(Event(title=title, date=date_iso or ""))

        # Evaluations (fallback to heuristic if empty)
        evals_out: list[Assessment] = []
        for ev in result.evaluations or []:
            name = (ev.name or "").strip()
            weight = float(ev.weight) if ev.weight is not None else None
            if name and weight is not None and 0 <= weight <= 200:
                evals_out.append(Assessment(name=name, weight=weight))
        if not evals_out:
            evals_out = _extract_evaluations([l.strip() for l in text.splitlines()])

        # Normalize evaluations to ~100
        if evals_out:
            total = sum(e.weight for e in evals_out)
            if total > 0 and (total < 98 or total > 102):
                for e in evals_out:
                    e.weight = round(e.weight / total * 100, 2)
                diff = round(100 - sum(e.weight for e in evals_out), 2)
                if abs(diff) >= 0.05:
                    max_e = max(evals_out, key=lambda x: x.weight)
                    max_e.weight = round(max_e.weight + diff, 2)

        return ParseResult(summary=summary or "No summary returned.", events=events_out, evaluations=evals_out)
    except Exception as e:
        logger.exception("LangChain parse failed; using heuristic.")
        fb = heuristic(text)
        fb.summary = f"(Fallback due to error: {e})\n{fb.summary}"
        return fb
