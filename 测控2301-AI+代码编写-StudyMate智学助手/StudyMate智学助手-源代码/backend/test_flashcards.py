
from database import SessionLocal
from models import Note, Flashcard
import datetime

db = SessionLocal()

print("=== 检查数据库中的闪卡 ===")
flashcards = db.query(Flashcard).all()
print(f"总闪卡数量: {len(flashcards)}")
for fc in flashcards:
    print(f"ID: {fc.id}, 笔记ID: {fc.note_id}, 问题: {fc.question}, 答案: {fc.answer}")

print("\n=== 检查笔记 ===")
notes = db.query(Note).all()
print(f"总笔记数量: {len(notes)}")
for note in notes:
    print(f"ID: {note.id}, 标题: {note.title}")

db.close()
