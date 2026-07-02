import os
import shutil
import sys

def main():
    print("=== StudyMate 数据迁移工具 ===")
    
    # 1. 找到所有可能的数据库位置
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 可能的数据库位置
    possible_dbs = [
        os.path.join(project_root, 'data', 'studymate.db'),
        os.path.join(project_root, 'backend', 'data', 'studymate.db'),
        os.path.join(project_root, 'backend', 'studymate.db'),
        os.path.join(project_root, 'studymate.db'),
    ]
    
    print("\n正在搜索数据库文件...")
    found_dbs = []
    for db_path in possible_dbs:
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"  ✓ 找到: {db_path} (大小: {size:,} 字节)")
            found_dbs.append((db_path, size))
    
    if not found_dbs:
        print("  ✗ 未找到任何数据库文件")
        return
    
    # 2. 找到最大的数据库
    largest_db = max(found_dbs, key=lambda x: x[1])
    print(f"\n最大的数据库: {largest_db[0]}")
    
    # 3. 创建用户数据目录
    app_data_dir = os.path.join(os.environ['APPDATA'], 'StudyMate')
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
    
    target_db = os.path.join(app_data_dir, 'studymate.db')
    
    # 4. 复制数据库
    print(f"\n正在复制到用户数据目录: {target_db}")
    
    if os.path.exists(target_db):
        backup_path = target_db + '.backup'
        print(f"  备份现有数据库到: {backup_path}")
        shutil.copy2(target_db, backup_path)
    
    shutil.copy2(largest_db[0], target_db)
    
    print("✓ 数据迁移完成！")
    
    # 验证一下
    print("\n验证迁移结果...")
    import sqlite3
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM courses")
        count = cursor.fetchone()[0]
        print(f"  ✓ 数据库中有 {count} 个课程")
        
        cursor.execute("SELECT id, name FROM courses")
        courses = cursor.fetchall()
        for c in courses:
            print(f"    - {c[1]} (ID: {c[0]})")
    except Exception as e:
        print(f"  ✗ 验证出错: {e}")
    finally:
        conn.close()
    
    print("\n现在请重新打开 StudyMate，你应该能看到所有数据了！")

if __name__ == '__main__':
    main()
