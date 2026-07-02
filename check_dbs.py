import sqlite3
import os

def check_db(path):
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        return tables
    return None

db_paths = [
    'd:/studymate/backend/study_mate.db',
    'd:/studymate/backend/studymate.db',
    'd:/studymate/studymate.db'
]

for path in db_paths:
    tables = check_db(path)
    if tables:
        print(f"\n=== {path} ===")
        print("表列表:", [t[0] for t in tables])
    else:
        print(f"\n=== {path} ===")
        print("文件不存在或为空")