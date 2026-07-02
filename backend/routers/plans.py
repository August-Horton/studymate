import asyncio
import json
import re
import datetime
from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel
from fastapi import APIRouter
from ai.client import chat_completion 

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import SessionLocal, Base
from models import StudyPlan

router = APIRouter()

# ================= 1. 请求模型定义 =================
class QuestionnaireRequest(BaseModel):
    course_id: int
    course_name: str = "未知课程"
    exam_date: date
    target_score: float = 100.0
    question_count: int = 10

class NextQuestionnaireRequest(BaseModel):
    course_name: str
    exam_date: date
    target_score: float = 100.0
    grade: Optional[str] = "未提供"
    previous_answers: List[dict] = []
    current_round: int = 1
    question_count: int = 10

class AnswersRequest(BaseModel):
    course_name: str
    exam_date: date
    target_score: float = 100.0
    daily_hours: float = 3.0
    mastery: int = 5
    weak_points: str = ""
    all_answers: List[dict] = []

class DetailPlanRequest(BaseModel):
    course_name: str
    exam_date: date
    target_score: float = 100.0
    daily_hours: float = 3.0
    weak_points: str = ""
    mastery: int = 5

class DailyDetailRequest(BaseModel):
    course_name: str
    date: str
    task_summary: str
    custom_requirement: Optional[str] = ""

class RescuePlanRequest(BaseModel):
    course_name: str
    exam_date: date
    missed_topics: str

# ================= 2. 强力安全解析工具 =================
def ultra_safe_parse(text):
    """提取纯 JSON 数组 [...]，防崩溃"""
    try:
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            clean_json = match.group()
            # 清理可能存在的代码块标记
            clean_json = clean_json.replace('\n', '')
            # 处理可能的 markdown 代码块包裹
            if clean_json.startswith('```json'):
                clean_json = clean_json[7:]
            if clean_json.endswith('```'):
                clean_json = clean_json[:-3]
            return json.loads(clean_json)
    except Exception as e:
        print(f"DEBUG: 数组解析失败: {str(e)}")
        return None
    return None

def ultra_safe_parse_dict(text):
    """提取纯 JSON 对象 {...}，保留换行符，用于提取长篇备考建议"""
    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            clean_json = match.group()
            return json.loads(clean_json)
    except Exception as e:
        print(f"DEBUG: 字典解析失败: {str(e)}")
        return None
    return None

# ================= 3. 核心业务路由 =================
@router.post("/next_questionnaire")
async def generate_next_questionnaire(req: NextQuestionnaireRequest):
    """进化版三轮诊断路由"""
    history_context = ""
    for r in req.previous_answers:
        history_context += f"第{r.get('round')}轮调研结果: {str(r.get('answers'))}\n"

    if req.current_round == 1:
        prompt = f"""你是一位资深学业规划导师。请为当前年级为【{req.grade}】的学生生成 {req.question_count} 道关于《{req.course_name}》的【宏观学情与备考规划调研题】。
        【绝对禁止】出现具体的数学公式、计算题、知识点测试！
        【题型要求】
        1. 必须有一道题 type 为 "multiple"（多选题），问："在《{req.course_name}》中，你目前最头疼的哪几个板块？（可多选）"。选项必须符合该学科特性。
        2. 必须有一道单选题明确问：本次备考是希望进行"专项突破"（针对特定薄弱章节）还是"整体训练"（全面系统复习）？
        3. 其他题目（"single"单选）调研复习时间、历史成绩等。
        【输出格式】纯JSON数组：[{{"id":1, "question":"...", "type":"single|multiple", "options":["A...","B..."]}}]"""
        
    elif req.current_round == 2:
        prompt = f"""你是一位备考心理与规划专家。以下是学生第一轮的回答：
        {history_context}
        【出题逻辑】
        1. 仔细分析回答，如果上轮选了"专项突破"，本轮必须设置多选题（"multiple"）追问想突破哪几个具体模块。
        2. 如果选了"整体训练"，侧重调研其全局复习节奏和时间规划。
        【注意】禁止出现具体考题！纯粹调研偏好。
        【输出格式】纯JSON数组：[{{"id":1, "question":"...", "type":"single|multiple|text", "options":["A..."]}}]"""
        
    else:
        prompt = f"""你现在是《{req.course_name}》的命题组组长。结合前两轮的倾向（特别是专项突破的章节）：
        {history_context}
        请出具 {req.question_count} 道高质硬核真题/模拟题。若之前选择了专项突破，题目必须集中在该专项领域。
        【输出格式】纯JSON数组，题型可以是 single 或 multiple。"""

    try:
        messages = [{"role": "user", "content": prompt}]
        timeout_limit = 45.0 if req.current_round == 3 else 25.0
        ai_task = chat_completion(messages, temperature=0.5, max_tokens=3000)
        ai_response = await asyncio.wait_for(ai_task, timeout=timeout_limit)
        
        questions = ultra_safe_parse(ai_response)
        if questions and len(questions) > 0:
            return {"questions": questions, "round": req.current_round}
            
        raise Exception("无法提取有效问卷 JSON 数组")
    except Exception as e:
        print(f"DEBUG: 第{req.current_round}轮生成异常: {str(e)}")
        return {"error": True, "message": f"第{req.current_round}轮问卷AI生成失败，请重试。"}

@router.post("/generate_from_answers")
async def generate_from_answers(req: AnswersRequest):
    """基于诊断结果的深度计划生成"""
    today_str = date.today().strftime("%Y-%m-%d")
    days_left = (req.exam_date - date.today()).days
    if days_left <= 0:
        return {"error": True, "message": "考试日期必须是将来的日期"}

    answers_desc = "\n".join([f"第{r.get('round')}轮: {r.get('answers')}" for r in req.all_answers])

    prompt = f"""你是一位全国顶尖的学科教研组长。请定制《{req.course_name}》每日备考计划。
    
    【核心时间线约束 - 必须绝对服从】
    - 计划起点（今天）：{today_str}
    - 计划终点（考试）：{req.exam_date}
    - 备考总天数：{days_left}天
    你的计划必须从 {today_str} 开始排期！

    【学生核心数据】{answers_desc}
    【学科防伪预警 - 绝对执行】使用《{req.course_name}》的专属名词！文科绝对不许提"公式/计算"！
    【拒绝机械重复】绝对不接受连续多天出现相同的任务描述。每一天都必须拆解出具体的动作。
    【全局备考心法】在JSON最外层增加 overall_advice 字段，字数约200字，给出专业、鼓励、直击痛点的宏观复习建议。
    
    【输出格式】严格输出纯JSON对象：
    {{
      "overall_advice": "针对该考生的总体备考心法...",
      "phases": [
        {{"name": "阶段名称", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "focus": "目标"}}
      ],
      "daily_plan": {{
        "{today_str}": "【具体模块】复习动作（今天第一天的任务）",
        "这里按真实日历日期连续递增直到 {req.exam_date}": "每天的任务描述..."
      }}
    }}"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        ai_task = chat_completion(messages, temperature=0.6, max_tokens=4000)
        ai_response = await asyncio.wait_for(ai_task, timeout=120.0)
        plan_data = ultra_safe_parse_dict(ai_response)
        
        if plan_data and "daily_plan" in plan_data:
            return plan_data
        raise Exception("AI 生成内容无法解析为计划字典对象")
    except Exception as e:
        print(f"!!! [CRITICAL] 计划定制解析失败: {str(e)}")
        return {"error": True, "message": "AI 导师定制计划超时或解析失败，请点击重新生成。"}

@router.post("/rescue_plan")
async def generate_rescue_plan(req: RescuePlanRequest):
    """进度告急：动态抢救计划生成"""
    today_str = date.today().strftime("%Y-%m-%d")
    days_left = (req.exam_date - date.today()).days
    if days_left <= 0:
        return {"error": True, "message": "考试即将开始或已结束，请调整心态，全力冲刺！"}

    prompt = f"""你是一位极致温柔且专业的全国顶尖学科教研组长。你的学生正在备考《{req.course_name}》。
    【危机情况】学生最近进度落后了，心里非常焦虑。以下是他前段时间落下/未完全掌握的核心任务摘要：
    {req.missed_topics if req.missed_topics else "基础复习进度整体滞后"}

    【抢救任务】请在不改变考试日期（{req.exam_date}）的前提下，为他重新排布从今天（{today_str}）到考试前的每一天复习计划。
    要求：
    1. 必须包含之前落下的关键内容，并将其科学压缩、分配到接下来的 {days_left} 天里。
    2. 每天的任务描述必须具体（约30字，每天不同）。
    3. 【核心情绪价值】在 overall_advice 字段写一段极具安抚力量的话（约150字），明确告诉他："别灰心，我已经帮你调整了最优路径，把落下的重点重新排布了，现在开始一切都来得及！"

    【输出格式】严格输出纯JSON对象：
    {{
      "overall_advice": "安抚情绪的寄语...",
      "daily_plan": {{
        "{today_str}": "【抢救启动】今天的复习动作...",
        "日期递增直到 {req.exam_date}": "每天的任务描述..."
      }}
    }}"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        ai_task = chat_completion(messages, temperature=0.6, max_tokens=3000)
        ai_response = await asyncio.wait_for(ai_task, timeout=90.0)
        plan_data = ultra_safe_parse_dict(ai_response)
        
        if plan_data and "daily_plan" in plan_data:
            return plan_data
        raise Exception("抢救计划解析失败")
    except Exception as e:
        print(f"DEBUG: 抢救计划失败: {str(e)}")
        return {"error": True, "message": "AI 导师正在休息，请稍后再试。"}

@router.post("/daily_detail")
async def generate_daily_detail(req: DailyDetailRequest):
    """单日微观计划深度拆解（支持定向重载与打卡提取）"""
    
    requirement_text = ""
    if req.custom_requirement and req.custom_requirement.strip():
        requirement_text = f"\n    【学生给你的特别定制要求】：{req.custom_requirement}\n    请你务必严格按照这条要求，对今天的任务清单和复习方法进行重构！"

    prompt = f"""你是一名严厉且专业的金牌导师。学生正在备考《{req.course_name}》。
    【今日核心任务】：{req.task_summary}
    {requirement_text}
    
    请为他今天的这单项任务，制定一份极度硬核的微观执行清单。包含：时间段拆解、具体复习方法、常见易错坑点。
    
    【输出格式要求 - 绝对执行】
    1. 必须在开头生成一个名为"🚀 今日微任务"的清单。清单中的每一项具体任务，必须严格以 "- [ ] " 开头（注意中括号里有空格，且后面紧跟一个空格）。例如："- [ ] 上午：精读1篇真题阅读"。
    2. 任务清单下方，再用排版优美的 Markdown 文本输出具体的方法指导和易错坑点分析。
    不要写任何 JSON，不要有代码块包裹，直接输出纯文本。"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        ai_task = chat_completion(messages, temperature=0.6, max_tokens=2000)
        ai_response = await asyncio.wait_for(ai_task, timeout=30.0)
        
        clean_text = re.sub(r'^```markdown\s*', '', ai_response, flags=re.MULTILINE)
        clean_text = re.sub(r'^```\s*$', '', clean_text, flags=re.MULTILINE)
        clean_text = clean_text.strip()
        
        return {"detail": clean_text}
    except asyncio.TimeoutError:
        return {"error": True, "message": "单日详情生成超时，请重试"}
    except Exception as e:
        print(f"DEBUG: 单日详情生成失败: {str(e)}")
        return {"error": True, "message": "单日详情生成失败，请重试。"}

# ================= 4. 计划持久化接口 =================
@router.get("/get_plan")
def get_plan(course_id: int, user_id: int = 1):
    """获取用户的备考计划"""
    db = SessionLocal()
    plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id,
        StudyPlan.course_id == course_id
    ).first()
    
    if plan:
        result = {
            "exam_date": plan.exam_date.strftime("%Y-%m-%d"),
            "target_score": plan.target_score,
            "daily_plan": json.loads(plan.daily_tasks) if plan.daily_tasks else {},
            "overall_advice": plan.overall_advice or ''
        }
        db.close()
        return {"success": True, "data": result}
    
    db.close()
    return {"success": False, "message": "未找到计划"}

class SavePlanRequest(BaseModel):
    course_id: int
    user_id: Optional[int] = 1
    exam_date: str
    target_score: float
    daily_plan: str
    overall_advice: Optional[str] = ""

@router.post("/save_plan")
def save_plan(req: SavePlanRequest):
    """保存备考计划到数据库"""
    db = SessionLocal()
    
    # 先检查是否已有该课程的计划
    existing_plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == req.user_id,
        StudyPlan.course_id == req.course_id
    ).first()
    
    try:
        exam_date_parsed = datetime.datetime.strptime(req.exam_date, "%Y-%m-%d").date()
        
        if existing_plan:
            # 更新现有计划
            existing_plan.exam_date = exam_date_parsed
            existing_plan.target_score = req.target_score
            existing_plan.daily_tasks = req.daily_plan
            existing_plan.overall_advice = req.overall_advice
        else:
            # 创建新计划
            new_plan = StudyPlan(
                user_id=req.user_id,
                course_id=req.course_id,
                exam_date=exam_date_parsed,
                target_score=req.target_score,
                daily_tasks=req.daily_plan,
                overall_advice=req.overall_advice
            )
            db.add(new_plan)
        
        db.commit()
        db.close()
        return {"success": True, "message": "计划保存成功"}
    
    except Exception as e:
        db.rollback()
        db.close()
        print(f"DEBUG: 保存计划失败: {str(e)}")
        return {"error": True, "message": f"保存失败: {str(e)}"}
