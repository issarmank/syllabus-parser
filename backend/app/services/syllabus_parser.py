# app/services/syllabus_parser.py
from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def parse_syllabus(text: str):
    prompt = f"""
    You are an assistant that extracts schedules from university syllabuses.
    Extract all assignments, exams, and deadlines into JSON format:

    {{
      "assignments": [
        {{ "title": "...", "due_date": "YYYY-MM-DD" }}
      ],
      "exams": [
        {{ "name": "Midterm", "date": "YYYY-MM-DD" }}
      ],
      "other": [...]
    }}

    Syllabus content:
    {text}
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
