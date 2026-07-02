from fastapi import APIRouter, HTTPException
from database import SessionLocal
from models import Course, Note, Flashcard
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class CourseCreate(BaseModel):
    name: str
    knowledge_points: str = "[]"

class CourseUpdate(BaseModel):
    name: str = None
    knowledge_points: str = None

@router.get("/")
def get_courses(user_id: int = 1):
    db = SessionLocal()
    try:
        courses = db.query(Course).filter(Course.user_id == user_id).all()
        if not courses:
            # 如果数据库为空，返回一个硬编码的测试课程
            print("[DEBUG] 数据库无课程，返回测试课程")
            return [{"id": 1, "name": "高等数学(故障恢复模式)", "knowledge_points": "[]"}]
        print(f"[DEBUG] 返回 {len(courses)} 个课程")
        return courses
    except Exception as e:
        print(f"[ERROR] 课程查询失败: {e}")
        # 异常时也返回测试课程
        return [{"id": 1, "name": "高等数学(故障恢复模式)", "knowledge_points": "[]"}]
    finally:
        db.close()

@router.post("/")
def create_course(course: CourseCreate, user_id: int = 1):
    db = SessionLocal()
    new_course = Course(user_id=user_id, name=course.name, knowledge_points=course.knowledge_points)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    db.close()
    return new_course

@router.put("/{course_id}")
def update_course(course_id: int, course: CourseUpdate, user_id: int = 1):
    db = SessionLocal()
    db_course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if not db_course:
        db.close()
        raise HTTPException(status_code=404, detail="课程不存在")
    if course.name is not None:
        db_course.name = course.name
    if course.knowledge_points is not None:
        db_course.knowledge_points = course.knowledge_points
    db.commit()
    db.refresh(db_course)
    db.close()
    return db_course

@router.delete("/{course_id}")
def delete_course(course_id: int, user_id: int = 1):
    db = SessionLocal()
    # 查找课程
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if not course:
        db.close()
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 级联删除该课程下的所有笔记和闪卡
    notes = db.query(Note).filter(Note.course_id == course_id, Note.user_id == user_id).all()
    for note in notes:
        # 删除笔记下的闪卡
        db.query(Flashcard).filter(Flashcard.note_id == note.id).delete()
    # 删除所有笔记
    db.query(Note).filter(Note.course_id == course_id, Note.user_id == user_id).delete()
    
    # 同时删除该课程下直接关联的闪卡（如果有）
    db.query(Flashcard).filter(Flashcard.course_id == course_id, Flashcard.user_id == user_id).delete()
    
    # 最后删除课程本身
    db.delete(course)
    db.commit()
    db.close()
    return {"message": "课程及关联数据已删除"}

@router.get("/{course_id}/flashcards")
def get_course_flashcards(course_id: int, user_id: int = 1):
    db = SessionLocal()
    cards = db.query(Flashcard).filter(
        Flashcard.course_id == course_id,
        Flashcard.user_id == user_id
    ).all()
    result = []
    for c in cards:
        result.append({
            "id": c.id,
            "question": c.question,
            "answer": c.answer,
            "ease_factor": c.ease_factor,
            "interval": c.interval,
            "next_review_date": c.next_review_date.isoformat() if c.next_review_date else None
        })
    db.close()
    return result

@router.delete("/flashcards/{card_id}")
def delete_flashcard(card_id: int, user_id: int = 1):
    db = SessionLocal()
    card = db.query(Flashcard).filter(Flashcard.id == card_id, Flashcard.user_id == user_id).first()
    if not card:
        db.close()
        raise HTTPException(status_code=404, detail="闪卡不存在")
    db.delete(card)
    db.commit()
    db.close()
    return {"message": "已删除"}