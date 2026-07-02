from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timedelta
from database import SessionLocal
from models import Flashcard

router = APIRouter()

class ReviewRequest(BaseModel):
    card_id: int
    quality: int

@router.post("/review")
def review_card(req: ReviewRequest):
    db = SessionLocal()
    card = db.query(Flashcard).filter(Flashcard.id == req.card_id).first()
    if not card:
        db.close()
        return {"error": "not found"}

    if req.quality < 3:
        card.interval = 1
        card.ease_factor = max(1.3, card.ease_factor - 0.2)
    else:
        if card.interval == 0:
            card.interval = 1
        elif card.interval == 1:
            card.interval = 6
        else:
            card.interval = round(card.interval * card.ease_factor)
        card.ease_factor = card.ease_factor + (0.1 - (5 - req.quality) * (0.08 + (5 - req.quality) * 0.02))
        if card.ease_factor < 1.3:
            card.ease_factor = 1.3

    card.next_review_date = datetime.now() + timedelta(days=card.interval)
    db.commit()
    db.close()
    return {"next_review": card.next_review_date.isoformat()}