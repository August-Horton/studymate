import sqlite3

db_path = "studymate.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 添加 target_score 列
    print("正在添加 target_score 列...")
    cursor.execute("ALTER TABLE study_plans ADD COLUMN target_score REAL")
    conn.commit()
    print("✅ target_score 列添加成功！")

    # 再次检查表结构
    print("\n=== 更新后的 study_plans 表结构 ===")
    cursor.execute("PRAGMA table_info(study_plans)")
    for column in cursor.fetchall():
        print(column)

except Exception as e:
    print(f"错误: {e}")
finally:
    conn.close()
