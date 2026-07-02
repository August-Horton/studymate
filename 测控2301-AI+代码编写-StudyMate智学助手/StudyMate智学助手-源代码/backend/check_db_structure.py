import sqlite3

db_path = "studymate.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查 study_plans 表结构
print("=== study_plans 表结构 ===")
cursor.execute("PRAGMA table_info(study_plans)")
for column in cursor.fetchall():
    print(column)

print("\n=== study_plans 表数据 ===")
cursor.execute("SELECT * FROM study_plans")
for row in cursor.fetchall():
    print(row)

conn.close()
