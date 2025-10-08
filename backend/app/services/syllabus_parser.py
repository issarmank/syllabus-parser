import re
from datetime import datetime
from typing import Optional
from pypdf import PdfReader
from io import BytesIO
from app.models import ParseResult, Event, Assessment

try:
    from openai import OpenAI
    from pydantic import BaseModel, Field
    from app.config import OPENAI_API_KEY
    HAS_OPENAI = bool(OPENAI_API_KEY)
except ImportError:
    HAS_OPENAI = False
    print("WARNING: OpenAI not available. Install with: pip install openai")

# Use pydantic v2 (standard BaseModel)
class LcEvent(BaseModel):
    """Event with title and date."""
    title: str = Field(description="Event name (e.g., 'Assignment 1', 'Midterm Exam')")
    date: str = Field(description="Date in YYYY-MM-DD format")

class LcAssessment(BaseModel):
    """Assessment category with weight."""
    name: str = Field(description="Assessment category name (e.g., 'Assignments (5)', 'Final Exam')")
    weight: int = Field(description="Percentage weight (0-100)")

class LcSyllabus(BaseModel):
    """Parsed syllabus structure."""
    summary: str = Field(description="2-4 sentence course overview")
    events: list[LcEvent] = Field(default_factory=list, description="Individual deadlines with specific dates")
    evaluations: list[LcAssessment] = Field(default_factory=list, description="Assessment categories with weights that sum to 100")

SYSTEM = (
    "You are an expert at parsing university course syllabi. Extract the following information:\n\n"
    "1. SUMMARY: Write a clear 2-4 sentence overview of the course including:\n"
    "   - Course subject and level\n"
    "   - Main topics covered\n"
    "   - Learning approach or format\n\n"
    "2. EVENTS: Extract ONLY individual deadlines with SPECIFIC dates. Include:\n"
    "   - Assignment deadlines (e.g., 'Assignment 1' on '2025-09-23')\n"
    "   - Quiz/Test dates (e.g., 'Midterm Test' on '2025-10-15')\n"
    "   - Exam dates (e.g., 'Final Exam' on '2025-12-10')\n"
    "   - Project milestones with dates\n"
    "   DO NOT include recurring weekly items or items without specific dates.\n"
    "   Format ALL dates as YYYY-MM-DD.\n\n"
    "3. EVALUATIONS: Extract assessment CATEGORIES (not individual instances) with their total weights:\n"
    "   Examples:\n"
    "   - 'Assignments (5)' with weight 30 (if there are 5 assignments worth 30% total)\n"
    "   - 'Labs (10 of 12)' with weight 10 (best 10 of 12 labs worth 10% total)\n"
    "   - 'Midterm Test' with weight 20\n"
    "   - 'Final Exam' with weight 40\n"
    "   IMPORTANT:\n"
    "   - Extract category names EXACTLY as they appear, including counts in parentheses\n"
    "   - Weight should be the TOTAL percentage for that category (just the number, no % sign)\n"
    "   - ALL weights MUST sum to exactly 100\n"
    "   - If weights don't sum to 100 in the source, normalize them proportionally\n"
    "   - Include ONLY graded assessment categories, not participation or attendance unless graded\n\n"
    "Be precise and only extract information that is clearly stated in the syllabus."
)

def parse_syllabus_from_pdf(file_bytes: bytes) -> ParseResult:
    """Parse syllabus PDF using AI extraction."""
    
    # Extract text from PDF
    try:
        reader = PdfReader(BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return ParseResult(
            summary=f"Error reading PDF: {str(e)}",
            events=[],
            evaluations=[]
        )

    if not text.strip():
        return ParseResult(
            summary="Empty or unreadable PDF",
            events=[],
            evaluations=[]
        )

    # Check if AI parsing is available
    if not HAS_OPENAI:
        return ParseResult(
            summary="AI parsing not available. Please set OPENAI_API_KEY in your .env file.",
            events=[],
            evaluations=[]
        )

    # Use AI to parse the syllabus
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Parse this syllabus:\n\n{text}"}
            ],
            response_format=LcSyllabus,
            temperature=0
        )
        
        result = completion.choices[0].message.parsed
        
        # Convert to our models
        events = [Event(title=e.title, date=e.date) for e in result.events]
        evaluations = [Assessment(name=a.name, weight=a.weight) for a in result.evaluations]
        
        # Post-process evaluations to ensure weights sum to exactly 100
        if evaluations:
            total = sum(a.weight for a in evaluations)
            
            if total == 0:
                # Invalid data, return empty
                evaluations = []
            elif total != 100:
                # Normalize weights proportionally
                normalized_evaluations = []
                for a in evaluations:
                    normalized_weight = round((a.weight / total) * 100)
                    if normalized_weight > 0:
                        normalized_evaluations.append(Assessment(name=a.name, weight=normalized_weight))
                
                evaluations = normalized_evaluations
                
                # Fix rounding errors to ensure exactly 100%
                current_sum = sum(a.weight for a in evaluations)
                diff = 100 - current_sum
                
                if diff != 0 and evaluations:
                    # Add difference to the largest item
                    largest = max(evaluations, key=lambda a: a.weight)
                    largest.weight += diff
        
        return ParseResult(
            summary=result.summary or "No summary available",
            events=events,
            evaluations=evaluations
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"AI parsing error: {error_msg}")
        
        # Check if it's an API key error
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return ParseResult(
                summary="OpenAI API key is invalid or not set. Please check your .env file.",
                events=[],
                evaluations=[]
            )
        
        return ParseResult(
            summary=f"AI parsing failed: {error_msg}",
            events=[],
            evaluations=[]
        )
