from fastapi import APIRouter
from pydantic import BaseModel
from ai.client import chat_completion

router = APIRouter()

class PaperRequest(BaseModel):
    text: str

@router.post("/polish")
async def polish_paper(req: PaperRequest):
    prompt = f"请对以下学术文本进行语法校对和学术风格优化：\n{req.text}"
    messages = [{"role": "user", "content": prompt}]
    polished = await chat_completion(messages)
    return {"original": req.text, "polished": polished}