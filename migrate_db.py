import os
import shutil

def main():
    # 定义路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 现有的数据库文件
    old_db_paths = [
        os.path.join(project_root, 'studymate.db'),
        os.path.join(project_root, 'backend', 'studymate.db'),
        os.path.join(project_root, 'backend', 'data', 'studymate.db')
    ]
    
    # 新的统一数据库位置
    new_data_dir = os.path.join(project_root, 'data')
    new_db_path = os.path.join(new_data_dir, 'studymate.db')
    
    # 确保新目录存在
    if not os.path.exists(new_data_dir):
        os.makedirs(new_data_dir)
    
    # 找到最大的数据库文件（通常包含最新数据）
    largest_db = None
    largest_size = 0
    
    for db_path in old_db_paths:
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"找到数据库: {db_path} (大小: {size} 字节)")
            if size > largest_size:
                largest_size = size
                largest_db = db_path
    
    if largest_db:
        print(f"\n将最新数据库 ({largest_db}) 迁移到 {new_db_path}")
        
        if os.path.exists(new_db_path):
            backup_path = new_db_path + '.backup'
            print(f"目标文件已存在，备份到 {backup_path}")
            shutil.copy2(new_db_path, backup_path)
        
        shutil.copy2(largest_db, new_db_path)
        print("迁移完成！")
        
        # 删除旧的数据库文件（可选）
        print("\n是否删除旧的数据库文件？(y/n):")
        # 这里可以添加用户输入确认
    else:
        print("未找到任何数据库文件")

if __name__ == '__main__':
    main()
