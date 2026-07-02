from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import notes, papers, plans, review, courses, images
from ai.client import chat_completion
from pydantic import BaseModel
from datetime import date, timedelta
import json, re, random, time, logging
import sys
import os

# 配置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StudyMate-Audit")

# 获取资源路径 - 适配打包环境
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

app = FastAPI(title="StudyMate")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 全链路日志中间件
@app.middleware("http")
async def audit_log(request, call_next):
    start_time = time.time()
    logger.info(f"--- 请求开始: {request.method} {request.url.path} ---")
    print(f"[AUDIT] 请求开始: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"--- 请求完成: 状态码 {response.status_code} | 耗时 {process_time:.2f}s ---")
        print(f"[AUDIT] 请求完成: {request.method} {request.url.path} | 状态码 {response.status_code} | 耗时 {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"!!! 后端崩溃: {str(e)} | 耗时 {process_time:.2f}s", exc_info=True)
        print(f"[AUDIT ERROR] 后端崩溃: {request.method} {request.url.path} | 错误: {str(e)} | 耗时 {process_time:.2f}s")
        raise e

init_db()

# 测试路由 - 验证后端连通性
@app.get("/api/test-connection")
def test_conn():
    return {"status": "ok", "message": "Backend is reachable"}

def safe_parse_json(text):
    """安全解析JSON，处理非法转义字符"""
    try:
        # 先尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 替换常见的非法转义为可解析形式
        cleaned = text
        # 将反斜杠后跟非合法转义字符的情况，转为双反斜杠
        cleaned = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', cleaned)
        # 处理不完整的 \u 转义
        cleaned = re.sub(r'\\u([0-9a-fA-F]{0,3})(?![0-9a-fA-F])', r'\\\\u\1', cleaned)
        try:
            return json.loads(cleaned)
        except:
            pass
    return None

def ultra_safe_parse_dict(text):
    """提取 JSON 对象，严禁乱删转义字符"""
    try:
        # 只提取大括号范围内的内容
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            clean_json = match.group()
            return json.loads(clean_json)
    except Exception as e:
        print(f"DEBUG: 字典解析失败: {str(e)}")
        return None
    return None

app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(plans.router, prefix="/api/plans", tags=["plans"])
app.include_router(images.router, prefix="/api/images", tags=["images"])

# ---------- AI 速读分析 API ----------
class ChatRequest(BaseModel):
    messages: list
    model: str = "deepseek-chat"

class PdfAnalysisRequest(BaseModel):
    text: str

@app.post("/api/ai/chat")
async def chat(req: ChatRequest):
    """通用AI对话接口"""
    try:
        messages = req.messages
        response = await chat_completion(messages, temperature=0.7, max_tokens=1000)
        return {"content": response}
    except Exception as e:
        logger.error(f"AI 对话失败: {str(e)}", exc_info=True)
        return {"error": True, "message": f"AI 对话失败: {str(e)}"}

@app.post("/api/ai/analyze-pdf")
async def analyze_pdf(req: PdfAnalysisRequest):
    """用 DeepSeek AI 分析 PDF 内容，生成五段论速读报告"""
    try:
        prompt = f"""你是一位专业的学术论文阅读助手。请根据下面提供的论文内容，按照以下五个部分进行总结，要求语言简洁、重点突出。

【论文内容】
{req.text}

【输出格式要求】
请严格按照以下 JSON 格式输出，不要任何其他说明文字：
{{
  "研究背景": "简要说明研究领域和问题背景",
  "研究目的": "明确说明研究要解决的问题或要达成的目标",
  "研究方法": "描述研究采用的主要方法、技术路线或实验设计",
  "核心结果": "总结研究的主要发现、数据或结论",
  "结论与启示": "说明研究的意义、价值和应用前景"
}}

要求：
1. 每个部分的内容要具体，不要笼统
2. 语言要专业但易懂
3. 每个部分 50-150 字
4. 严格 JSON 格式，不要 markdown 标记
"""
        
        messages = [{"role": "user", "content": prompt}]
        ai_response = await chat_completion(messages, temperature=0.3, max_tokens=3000)
        
        # 解析返回的 JSON
        result = ultra_safe_parse_dict(ai_response)
        if result:
            return {"success": True, "data": result}
        else:
            # 如果解析失败，尝试直接返回内容
            return {"success": False, "message": "AI 解析格式错误，请重试"}
            
    except Exception as e:
        logger.error(f"PDF 分析失败: {str(e)}", exc_info=True)
        return {"success": False, "message": f"分析失败: {str(e)}"}

class PlanGenerateRequest(BaseModel):
    course_id: int
    exam_date: date
    target_score: float = 100.0
    mastery: int = 5          # 1-10
    daily_hours: float = 2    # 每天可用小时
    weak_points: str = ""     # 薄弱点描述

@app.post("/api/plans/generate")
async def generate_plan(req: PlanGenerateRequest):
    today = date.today()
    days_left = (req.exam_date - today).days
    if days_left <= 0:
        return {"error": "考试日期必须是将来的日期"}

    # ---------- 尝试用 AI 生成详细计划 ----------
    try:
        prompt = f"""你是学习规划师。请根据下面学生信息，输出一个严格JSON，不要解释。
学生信息：
- 距离考试：{days_left} 天
- 目标分数：{req.target_score}
- 自我评分（1-10）：{req.mastery}
- 每天可用：{req.daily_hours} 小时
- 薄弱点：{req.weak_points if req.weak_points else "无特殊说明"}

JSON格式（每个日期 YYYY-MM-DD，任务描述字数30字左右，要具体）：
{{"days_left":{days_left},"daily_plan":{{"YYYY-MM-DD":"具体任务"}} }}

要求：前两天侧重薄弱基础，最后两天总复习+错题。直接输出JSON：
"""
        messages = [{"role": "user", "content": prompt}]
        ai_response = await chat_completion(messages)
        
        # 清理 markdown 代码块标记
        cleaned = ai_response.strip()
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            cleaned = '\n'.join(lines[1:])
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
        
        # 尝试提取 JSON
        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            plan_data = json.loads(cleaned[json_start:json_end])
            if "daily_plan" in plan_data:
                plan_data["target_score"] = req.target_score
                print(f"[DEBUG] AI计划成功，返回 {len(plan_data.get('daily_plan', {}))} 天")
                return plan_data
    except Exception as e:
        print(f"DEBUG: AI计划生成失败: {str(e)}")
        return {"error": True, "message": "AI 生成计划失败，请重试"}


# 问卷生成请求
class QuestionnaireRequest(BaseModel):
    course_id: int
    course_name: str = "未知课程"
    exam_date: date
    target_score: float = 100.0
    question_count: int = 10  # 新增：题目数量

# 多轮问卷请求模型


# 根据答案生成计划请求
class AnswersRequest(BaseModel):
    course_id: int
    course_name: str = "未知课程"
    exam_date: date
    target_score: float = 100.0
    daily_hours: float = 3.0
    mastery: int = 5
    weak_points: str = ""
    all_answers: list = []  # 所有轮次的答案
    answers: dict = {}      # 旧版单轮答案




@app.post("/api/plans/generate_from_answers")
async def generate_from_answers(req: AnswersRequest):
    today = date.today()
    days_left = (req.exam_date - today).days
    if days_left <= 0:
        return {"error": "考试日期必须是将来的日期"}

    # 构建历史答案描述
    answers_desc = "无"
    if req.all_answers:
        answers_desc = ""
        for r in req.all_answers:
            round_num = r.get("round", "?")
            ans = r.get("answers", [])
            answers_desc += f"第{round_num}轮: " + "; ".join([f"题{a.get('id','')}选{a.get('answer','')}" for a in ans]) + "\n"
    elif req.answers:
        answers_desc = json.dumps(req.answers, ensure_ascii=False)

    # 计算薄弱点专项天数
    weak_days = min(5, max(2, int(days_left * 0.3)))
    weak_days = max(2, weak_days)

    # 构建高质量提示词 - 精算型导师
    prompt = f"""你是一位全国顶尖的学科教研组长。请根据学生以下诊断记录，为其定制《{req.course_name}》每日备考计划。

    【学生诊断核心数据】
    {answers_desc}

    【学科防伪预警与拒绝重复死命令 - 绝对执行】
    1. 必须使用《{req.course_name}》的专属名词！英语绝对不许提"公式/计算"！
    2. 绝对不接受连续多天出现完全相同的任务描述。每一天都必须拆解出具体的动作。

    【必须包含全局备考心法】
    你必须在JSON最外层输出 'overall_advice' 字段，提供非常有建设性、直击痛点、字数约200字的备考建议。
    建议内容需包括：核心发力点、心态调整、以及规避该学科常见陷阱的提示。语气要专业且充满鼓励。

    【输出格式】纯JSON对象：
    {{
      "overall_advice": "一段针对该考生的总体备考心法和复习建议...",
      "phases": [{{"name": "阶段", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "focus": "目标"}}],
      "daily_plan": {{"YYYY-MM-DD": "【具体模块】具体的复习动作（不少于20字，必须每天不同）"}}
    }}
    """
    try:
        messages = [{"role": "user", "content": prompt}]
        ai_response = await chat_completion(messages, temperature=0.6, max_tokens=4000)
        print(f"[AI] 计划响应长度: {len(ai_response)}")
        
        plan_data = ultra_safe_parse_dict(ai_response)
        
        if plan_data and "daily_plan" in plan_data:
            print(f"[AI] 计划生成成功，包含 {len(plan_data['daily_plan'])} 天任务")
            return plan_data
        raise Exception("AI 生成的计划不符合 JSON 对象格式")
    except Exception as e:
        print(f"DEBUG: 计划生成失败: {str(e)}")
        # 坚决不给流水账！直接报错让前端感知！
        return {"error": True, "message": "AI 定制计划失败，请重试"}

# 新增：详细计划生成请求
class DetailPlanRequest(BaseModel):
    course_name: str           # 课程全称
    exam_date: date
    target_score: float = 100.0
    daily_hours: float = 3.0   # 每天可用小时
    weak_points: str = ""      # 薄弱点描述
    mastery: int = 5           # 1-10 自评

@app.post("/api/plans/detail")
async def generate_detail_plan(req: DetailPlanRequest):
    today = date.today()
    days_left = (req.exam_date - today).days
    if days_left <= 0:
        return {"error": "考试日期必须是将来的日期"}

    # 构建高质量提示词
    prompt = f"""你是一位顶尖的考研/高考备考规划专家，名叫"智学导师"。请根据学生信息，为他制定一份极度详细、可直接执行的每日复习计划。

【参考样例】（你必须输出类似结构的计划，但内容要针对"{req.course_name}"）
第一阶段：基础扫盲与知识重构（x月x日 - x月x日，共n天）
目标：记住所有核心公式，消除"看不懂题"的障碍。
核心任务：过一遍教材目录，手写章节框架；每天复习一章概念、定理、公式；整理专属公式本。
每日任务示例：
- 5月12日：梳理《{req.course_name}》目录，手写各章框架；复习第一章，背诵核心公式并默写；做课后习题基础部分。
- 5月13日：复习第二章概念和定理，重点理解XX的条件和使用场景；做课后习题10道。
- ...

第二阶段：题型专项突破（x月x日 - x月x日，共n天）
目标：分板块刷题，形成条件反射。
分块训练：
1. XX专题（2天）：重点做XX题，总结方法。
2. XX专题（3天）：攻克计算难点。
每日任务示例：...

第三阶段：真题实战与提速（x月x日 - x月x日，共n天）
目标：适应考试节奏，查漏补缺。
安排：隔天做一套完整真题并分析错题...

第四阶段：考前冲刺（x月x日 - x月x日，共n天）
目标：保持手感，强化记忆。
安排：每日默写公式、回顾错题本、做半套卷子保持熟练度...

【学生信息】
- 课程名称：{req.course_name}
- 距离考试：{days_left} 天
- 目标分数：{req.target_score} 分
- 自评基础（1-10）：{req.mastery}
- 每天可用时间：{req.daily_hours} 小时
- 薄弱点：{req.weak_points if req.weak_points else "未提供"}

【输出要求】
1. 根据天数自动划分3~5个阶段，写明起止日期和核心目标。
2. 每天任务必须极度具体，包含：复习的具体章节或知识点、方法、题量、预计耗时（匹配{req.daily_hours}小时），字数30~60字。
3. 针对薄弱点前多后少地分配时间。
4. 严格 JSON 格式：
{{"phases":[{{"phase_name":"...","goal":"...","tasks":{{"YYYY-MM-DD":"任务","YYYY-MM-DD":"任务",...}}}},...],"daily_plan":{{"YYYY-MM-DD":"任务","YYYY-MM-DD":"任务",...}}}}
直接输出 JSON，无其他文字。
"""
    try:
        messages = [{"role": "user", "content": prompt}]
        ai_response = await chat_completion(messages, temperature=0.4)
        plan_data = ultra_safe_parse_dict(ai_response)
        if plan_data and "daily_plan" in plan_data:
            return plan_data
        raise Exception("AI 生成的计划不符合 JSON 对象格式")
    except Exception as e:
        print(f"DEBUG: 详细计划生成失败: {str(e)}")
        return {"error": True, "message": "AI 详细计划生成失败，请重试"}

if __name__ == "__main__":
    import uvicorn
    print("启动 StudyMate 后端服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
