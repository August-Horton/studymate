import sqlite3

# 使用正确的数据库路径
conn = sqlite3.connect('studymate.db')
print("使用数据库文件: studymate.db")

cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE notes ADD COLUMN tags TEXT DEFAULT ''")
    print("✓ 成功添加 tags 字段")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("✓ tags 字段已存在")
    else:
        print(f"错误: {e}")

conn.commit()
conn.close()
print("=== 操作完成 ===")