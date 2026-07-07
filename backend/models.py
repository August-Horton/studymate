from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    knowledge_points = Column(Text)  # JSON 存储

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    title = Column(String, nullable=True)
    original_text = Column(Text)
    structured_note = Column(Text)   # Markdown
    mindmap_json = Column(Text)
    tags = Column(String, default="")  # 逗号分隔的标签字符串
    folder = Column(String, default="默认笔记本")  # 文件夹归属
    pdf_source = Column(String)  # PDF 文件路径或标识
    pdf_page = Column(Integer)   # 摘录所在页码
    pdf_anchor = Column(String)  # 锚点文本标识
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    question = Column(Text)
    answer = Column(Text)
    ease_factor = Column(Float, default=2.5)
    interval = Column(Integer, default=0)
    next_review_date = Column(DateTime, default=datetime.datetime.utcnow)

class StudyPlan(Base):
    __tablename__ = "study_plans"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    exam_date = Column(DateTime)
    target_score = Column(Float)
    daily_tasks = Column(Text)  # JSON
    overall_advice = Column(Text)  # 备考建议
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class NoteLink(Base):
    __tablename__ = "note_links"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("notes.id"))
    target_title = Column(String)

class Literature(Base):
    __tablename__ = "literature"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    name = Column(String)
    filename = Column(String)
    filepath = Column(String)
    category_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
