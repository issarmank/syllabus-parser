from pydantic import BaseModel
from typing import List, Optional

class Event(BaseModel):
    title: str
    date: Optional[str] = None  # ISO YYYY-MM-DD or None/empty

class Assessment(BaseModel):
    name: str
    weight: float  # normalized percent (0-100)

class ParseResult(BaseModel):
    summary: str
    events: List[Event] = []
    evaluations: List[Assessment] = []  # NEW

class EventsResponse(BaseModel):
    events: List[Event] = []