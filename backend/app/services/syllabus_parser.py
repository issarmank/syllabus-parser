# app/services/syllabus_parser.py
import json, re
import logging
from openai import OpenAI
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

def extract_evaluations(text: str) -> list[Event]:  # placeholder type to allow earlier reference (will not be used)
    pass  # (dummy to quiet linters if any)

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

def parse_pdf_bytes(pdf_bytes: bytes, max_pages: int = 12) -> ParseResult:
    text = extract_text_from_pdf(pdf_bytes, max_pages=max_pages)
    if not text.strip():
        return ParseResult(summary="No text extracted.", events=[], evaluations=[])
    if not OPENAI_API_KEY:
        return heuristic(text)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text[:30000]},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        summary = (data.get("summary") or "").strip()

        # Events
        events_out: list[Event] = []
        for e in data.get("events", []):
            title = (e.get("title") or "").strip()
            date = (e.get("date") or "").strip()
            if date and not DATE_RE.match(date):
                continue
            if title:
                events_out.append(Event(title=title, date=date))
        # Evaluations from model (fallback to heuristic extraction if missing)
        evals_out = []
        for ev in data.get("evaluations", []):
            name = (ev.get("name") or "").strip()
            try:
                weight = float(ev.get("weight"))
            except Exception:
                continue
            if name and 0 <= weight <= 200:  # loose pre-normal check
                evals_out.append(Assessment(name=name, weight=weight))
        if not evals_out:
            evals_out = _extract_evaluations([l.strip() for l in text.splitlines()])

        # Normalize evaluations
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
        logger.exception("OpenAI parse failed; using heuristic.")
        fb = heuristic(text)
        fb.summary = f"(Fallback due to error: {e})\n{fb.summary}"
        return fb
