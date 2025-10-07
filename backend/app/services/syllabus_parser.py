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
    "- events MUST include a single concrete date; if multiple dates exist for the same item, create one event per date. Do not output events without dates.\n"
    "- evaluations: list each graded assessment component (e.g., 'Assignments', 'Midterm Exam', 'Final Examination', 'Project').\n"
    "- weight is its percentage of the final grade (number). Do NOT include % sign.\n"
    "- If separate undergraduate / graduate columns exist, prefer the undergraduate column. One weight per assessment.\n"
    "- Ensure evaluation weights sum approximately to 100 (adjust proportionally if raw data slightly off).\n"
    "- Exclude policy/administrative text such as late penalties, passing requirements, academic integrity, attendance, or 'Use of English'. Only graded components belong in 'evaluations'.\n"
    "- The 'summary' must be natural prose (2–4 sentences). Do not echo headings, bullet points, or table text."
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTHS = r"(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
DATE_TOKEN_RE = re.compile(rf"\b{MONTHS}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,\s*(\d{{4}}))?\b", re.IGNORECASE)

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
    allow_keywords = ("exam","midterm","final","quiz","assignment","project","due")
    for l in lines:
        low = l.lower()
        if not any(k in low for k in allow_keywords):
            continue
        iso_dates = _extract_iso_dates(l)
        if not iso_dates:
            continue
        # Use text before the first date as title (fallback to line)
        first_date_match = DATE_TOKEN_RE.search(l) or re.search(r"\b\d{4}-\d{2}-\d{2}\b", l)
        title = l[: first_date_match.start()].strip(" -:\t") if first_date_match else l
        title = (title or l)[:120]
        for d in iso_dates:
            events.append(Event(title=title, date=d))
        if len(events) >= 20:
            break
    evals = _extract_evaluations(lines)
    return ParseResult(summary=summary, events=events, evaluations=evals)


def _extract_evaluations(lines: list[str]) -> list[Assessment]:
    # Keep only lines likely to describe graded components and a percent
    percent_re = re.compile(r"(\d{1,3})(?:\s*%)")
    allow_keywords = re.compile(
        r"\b(assign(ment)?s?|mid[-\s]?term|final( exam| examination)?|quiz(zes)?|project(s)?|lab(s|oratory)?|participation|presentation|report|homework|tutorials?)\b",
        re.IGNORECASE,
    )
    deny_keywords = re.compile(
        r"\b(policy|penal(ties|ty)|late|plagiarism|integrity|attendance|passing|use of english|accommodat(ion|ions)|senate|appeal|grade(?:\s+of)?|less than|<|>)\b",
        re.IGNORECASE,
    )
    candidates: list[tuple[str, float]] = []
    for raw in lines:
        line = " ".join(raw.split())
        if not percent_re.search(line):
            continue
        if deny_keywords.search(line):
            continue
        if not allow_keywords.search(line):
            continue
        # Extract first percent as weight
        m = percent_re.search(line)
        if not m:
            continue
        weight = float(m.group(1))
        if not (0 < weight <= 100):
            continue
        # Name: take text before the percent, clean it up, shorten to ~6 words
        name = line
        # Common splits (tables: "Assessment  Weight")
        name = re.split(r"\s{2,}|\t|\s-\s|:\s", name)[0]
        name = re.sub(r"\s*\(*\d{1,3}\s*%\)*", "", name)
        name = re.sub(r"\s{2,}", " ", name).strip(" -:\t")
        # Normalize plurals like "3 assignments" -> "Assignments"
        name = re.sub(r"^\d+\s+", "", name).strip()
        # Limit overly long sentences
        words = name.split()
        if len(words) > 8:
            name = " ".join(words[:8])
        if len(name) < 3:
            continue
        candidates.append((name, weight))

    # Deduplicate by name (keep max weight)
    dedup: dict[str, float] = {}
    for n, w in candidates:
        dedup[n] = max(w, dedup.get(n, 0.0))
    rows = list(dedup.items())
    if not rows:
        return []
    # Normalize to 100 with minor rounding fix
    total = sum(w for _, w in rows)
    if total <= 0:
        return []
    normalized: list[Assessment] = [
        Assessment(name=n, weight=round((w / total) * 100, 2)) for n, w in rows
    ]
    diff = round(100 - sum(a.weight for a in normalized), 2)
    if abs(diff) >= 0.05:
        largest = max(normalized, key=lambda a: a.weight)
        largest.weight = round(largest.weight + diff, 2)
    # Keep at most 10 items
    return normalized[:10]


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


def _clean_text(s: str) -> str:
    # Fix hyphenation across line breaks and collapse whitespace
    s = re.sub(r"-\s*\n\s*", "", s)
    s = re.sub(r"\r", "\n", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _extract_iso_dates(text: str) -> list[str]:
    """Extract one or more dates from free text and normalize to ISO.
    Infers missing years from any year present in the same string."""
    if not text:
        return []
    out: list[str] = []

    # ISO tokens
    for iso in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text):
        out.append(iso)

    # Month Day (, Year) tokens, propagate year if only one provides it
    tokens = list(DATE_TOKEN_RE.finditer(text))
    if tokens:
        # find a year anywhere in the string
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
        inferred_year = year_match.group(1) if year_match else None
        for m in tokens:
            token = m.group(0)
            # ensure we have a year; if missing and we inferred one, append it
            if not re.search(r"\b(20\d{2}|19\d{2})\b", token) and inferred_year:
                token = re.sub(r"(?i)\b(st|nd|rd|th)\b", "", token)
                token = re.sub(r"\s*,?\s*$", f", {inferred_year}", token)
            iso = _to_iso(token)
            if iso:
                out.append(iso)

    # Dedup and sort
    out = sorted(set(out))
    return out

def parse_pdf_bytes(pdf_bytes: bytes, max_pages: int = 12) -> ParseResult:
    text = extract_text_from_pdf(pdf_bytes, max_pages=max_pages)
    text = _clean_text(text)
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

        # Events: split multi-date fields and keep only ISO-dated entries
        events_out: list[Event] = []
        for e in result.events or []:
            title = (e.title or "").strip()
            if not title:
                continue
            date_raw = (e.date or "").strip()
            iso_list = _extract_iso_dates(date_raw)
            for d in iso_list:
                events_out.append(Event(title=title, date=d))
        # If model returned none, try heuristic for events too
        if not events_out:
            events_out = heuristic(text).events

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

        return ParseResult(summary=summary or "No summary returned.", events=events_out[:20], evaluations=evals_out)
    except Exception as e:
        logger.exception("LangChain parse failed; using heuristic.")
        fb = heuristic(text)
        fb.summary = f"(Fallback due to error: {e})\n{fb.summary}"
        return fb
