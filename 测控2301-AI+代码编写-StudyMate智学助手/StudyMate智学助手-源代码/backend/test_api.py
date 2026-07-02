
import requests

base_url = "http://localhost:8000/api"

print("=== 测试闪卡API ===")
try:
    response = requests.get(f"{base_url}/notes/flashcards")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
except Exception as e:
    print(f"错误: {e}")
