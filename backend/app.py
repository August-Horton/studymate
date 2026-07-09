import uvicorn
import webbrowser
import threading
import time
import sys
import os

# 确保打包后能正确导入同级模块
if hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # 确保数据目录存在
    os.makedirs(get_resource_path("literature"), exist_ok=True)

    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 50)
    print("StudyMate 智学助手正在启动...")
    print("请稍候，浏览器将自动打开")
    print("=" * 50)

    # 直接导入 app 避免字符串引用在打包后失效
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
