from openai import AsyncOpenAI
import httpx
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StudyMate-Audit-AI")

# 默认配置（必须由前端传入 API Key，或通过环境变量配置）
DEFAULT_API_KEY = os.getenv("AI_API_KEY", "")
DEFAULT_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
DEFAULT_MODEL = os.getenv("AI_MODEL", "deepseek-v4")


def create_client(api_key=None, base_url=None):
    """根据传入的配置创建 OpenAI 兼容客户端"""
    actual_api_key = api_key or DEFAULT_API_KEY
    if not actual_api_key:
        raise RuntimeError("未配置 API Key，请在系统设置中配置或设置环境变量 AI_API_KEY")
    return AsyncOpenAI(
        api_key=actual_api_key,
        base_url=base_url or DEFAULT_BASE_URL,
        timeout=httpx.Timeout(1800.0, connect=10.0)
    )


async def chat_completion(
    messages,
    temperature=0.3,
    max_tokens=2000,
    model=None,
    api_key=None,
    base_url=None
):
    """
    调用大模型进行对话

    Args:
        messages: 对话消息列表
        temperature: 温度参数
        max_tokens: 最大输出 tokens
        model: 模型 ID（前端传入）
        api_key: API Key（前端传入）
        base_url: Base URL（前端传入）
    """
    actual_model = model or DEFAULT_MODEL
    logger.info(
        f"[AI] 发送请求，Provider: base_url={base_url or DEFAULT_BASE_URL}, "
        f"model={actual_model}, Prompt长度: {len(str(messages))}, "
        f"temperature={temperature}, max_tokens={max_tokens}"
    )
    try:
        # 每次调用创建新的 client，确保使用最新的配置
        client = create_client(api_key, base_url)

        response = await client.chat.completions.create(
            model=actual_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        content = response.choices[0].message.content
        logger.info(f"[AI] 响应成功，model={actual_model}，内容前100字: {content[:100]}...")
        return content
    except Exception as e:
        logger.error(f"[AI] API调用异常: {type(e).__name__} - {str(e)}")
        raise e
