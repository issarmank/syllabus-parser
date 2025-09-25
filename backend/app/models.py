from pydantic import BaseModel
from typing import List, Optional

class Event(BaseModel):
    title: str
    date: Optional[str] = None  # ISO YYYY-MM-DD or None/empty

class ParseResult(BaseModel):
    summary: str
    events: List[Event] = []

class EventsResponse(BaseModel):
    events: List[Event] = []