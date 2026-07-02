import sqlite3

# 连接数据库（尝试不同的数据库文件）
import os
db_files = ['study_mate.db', 'studymate.db']
conn = None

for db_file in db_files:
    if os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        print(f"使用数据库文件: {db_file}")
        break

if not conn:
    print("错误：找不到数据库文件")
    exit(1)
cursor = conn.cursor()

# 查看数据库中有哪些表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("数据库中的表:", tables)

# 查询所有笔记（查看当前状态）
cursor.execute("SELECT id, title, structured_note FROM notes")
notes = cursor.fetchall()

print("=== 当前笔记列表 ===")
for note in notes:
    note_id, title, content = note
    # 从内容提取标题
    lines = content.split('\n') if content else []
    content_title = ""
    for line in lines:
        if line.startswith('# '):
            content_title = line[2:].strip()
            break
    
    print(f"\nID: {note_id}")
    print(f"数据库 title: '{title}'")
    print(f"内容中的标题: '{content_title}'")
    
    # 如果数据库 title 为空，自动填入内容中的标题
    if not title and content_title:
        cursor.execute("UPDATE notes SET title = ? WHERE id = ?", (content_title, note_id))
        print(f"✓ 已自动填充标题: '{content_title}'")

conn.commit()
conn.close()
print("\n=== 操作完成 ===")