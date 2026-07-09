import os
import sys

# 获取应用数据目录 - 确保数据库路径始终一致
def get_app_data_dir():
    # 优先使用环境变量指定的目录
    if os.getenv('STUDYMATE_DATA_DIR'):
        app_data = os.getenv('STUDYMATE_DATA_DIR')
        try:
            os.makedirs(app_data, exist_ok=True)
            return app_data
        except:
            pass
    
    # 在开发模式下，使用项目根目录下的 data 文件夹
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        # 使用可执行文件所在目录的 data 文件夹
        try:
            exe_dir = os.path.dirname(sys.executable)
            app_data = os.path.join(exe_dir, 'data')
            os.makedirs(app_data, exist_ok=True)
            return app_data
        except:
            pass
        
        # 备用：使用用户数据目录
        try:
            app_name = 'StudyMate'
            if sys.platform == 'win32':
                app_data = os.path.join(os.environ['APPDATA'], app_name)
            elif sys.platform == 'darwin':
                app_data = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
            else:
                app_data = os.path.join(os.path.expanduser('~'), '.config', app_name)
            os.makedirs(app_data, exist_ok=True)
            return app_data
        except:
            pass
    
    # 开发环境：使用项目根目录下的 data 文件夹
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = os.path.dirname(backend_dir)
    app_data = os.path.join(app_root, 'data')
    os.makedirs(app_data, exist_ok=True)
    return app_data

app_data_dir = get_app_data_dir()
db_path = os.path.join(app_data_dir, 'studymate.db')

# 确保数据库目录存在
os.makedirs(os.path.dirname(db_path), exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

# 打印数据库路径用于调试
print(f"[DEBUG] Database path: {db_path}")

# AI 配置（仅通过环境变量设置，前端设置优先）
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
