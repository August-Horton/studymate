from database import SessionLocal
from models import Course

db = SessionLocal()

print("=== 检查数据库中的课程 ===")
courses = db.query(Course).all()
print(f"找到 {len(courses)} 个课程：")
for c in courses:
    print(f"  ID: {c.id}, Name: {c.name}, UserID: {c.user_id}")

db.close()
