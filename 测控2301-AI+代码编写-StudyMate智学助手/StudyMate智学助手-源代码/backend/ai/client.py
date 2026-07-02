from openai import AsyncOpenAI
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StudyMate-Audit-AI")

client = AsyncOpenAI(
    api_key="sk-be94e114ebb0492b955124ec67eaf2c3",
    base_url="https://api.deepseek.com/v1",
    timeout=httpx.Timeout(1800.0, connect=10.0)
)

async def chat_completion(messages, temperature=0.3, max_tokens=2000):
    logger.info(f"[AI] 发送请求，Prompt长度: {len(str(messages))}, temperature={temperature}, max_tokens={max_tokens}")
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        content = response.choices[0].message.content
        logger.info(f"[AI] 响应成功，内容前100字: {content[:100]}...")
        return content
    except Exception as e:
        logger.error(f"[AI] API调用异常: {type(e).__name__} - {str(e)}")
        raise e
