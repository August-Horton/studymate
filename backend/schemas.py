from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

class NoteOut(BaseModel):
    id: int
    user_id: int
    course_id: Optional[int]
    original_text: str
    structured_note: str
    mindmap_json: str
    created_at: datetime

    class Config:
        from_attributes = True

class FlashcardOut(BaseModel):
    id: int
    note_id: int
    user_id: int
    course_id: Optional[int]
    question: str
    answer: str
    ease_factor: float
    interval: int
    next_review_date: datetime

    class Config:
        from_attributes = True

class StudyPlanOut(BaseModel):
    id: int
    user_id: int
    course_id: Optional[int]
    exam_date: datetime
    daily_tasks: str

    class Config:
        from_attributes = True

class PaperPolishResponse(BaseModel):
    original: str
    polished: str
    reference_fix: str

class PlanGenerateResponse(BaseModel):
    course: str
    days_left: int
    daily_plan: dict
