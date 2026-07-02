from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy import or_, text
from database import SessionLocal
from models import Note, Flashcard
from pydantic import BaseModel
from typing import Optional
from ai.client import chat_completion
import json
import datetime
import re

router = APIRouter()

# ================ 全局定义：LaTeX 规范系统提示词 ================
latex_system = r"""你是一个严谨的高级学术笔记整理师。请严格按照以下格式规范生成笔记：

【排版绝对红线 - 违反将导致输出无效】
1. **Markdown 格式规范（必须严格遵守）**：
   - 标题必须另起一行，前面必须有空行！
   - ✅ 正确格式：
     
     上一段落的文字。
     
     ## 二级标题
     
     这是二级标题下的内容。
     
   - ❌ 错误格式：文字后面直接跟 ## 标题，中间没有空行
   - `##`、`###` 必须单独占一行，开头不能有空格或文字
2. **所有数学公式必须用美元符号包裹**：
   - 行内公式：必须用单个 $，例如：$a + b = c$、$\Delta > 0$、$\frac{a+b}{2}$
   - 独立区块公式：必须用 $$，例如：$$ax^2 + bx + c = 0$$
   - ❌ 绝对禁止出现没有包裹的裸露公式或希腊字母
3. **分数格式必须完美**：必须用 \frac{分子}{分母}（花括号不可省略！）
   - ✅ 正确：$\frac{a + b}{2}$
   - ❌ 错误：\frac a+b 2 或 \frac{a+b} 2
4. **平方根格式必须完美**：必须用 \sqrt{内容}（花括号不可省略！）
   - ✅ 正确：$\sqrt{ab}$
   - ❌ 错误：\sqrt ab
5. **希腊字母和运算符必须用 LaTeX 命令**
   - ✅ 正确：$\Delta$、$\alpha$、$\beta$、$\gamma$、$\geq$、$\leq$、$\neq$、$\pm$
   - ❌ 错误：直接用 Δ、α、β 等 Unicode 符号
6. **严禁使用 \( \) 或 \[ \] 这种格式**
7. **所有 LaTeX 命令后的花括号必须成对出现**
8. **禁止出现任何占位符如 [主题名称]、[定义] 等**
9. **直接输出整洁的 Markdown 文本，不需要额外解释**

【完美示例】
这是开头的介绍文字。

# 一元二次方程

## 1. 一般形式

一元二次方程的标准形式为：
$$ax^2 + bx + c = 0$$

其中 $a$、$b$、$c$ 为常数，且 $a \neq 0$。

## 2. 求根公式

通过配方法推导，求根公式为：
$$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

## 3. 判别式

判别式定义为：
$$\Delta = b^2 - 4ac$$

根据 $\Delta$ 的取值，根的情况分为三种：
- 当 $\Delta > 0$ 时：方程有两个不相等的实数根
- 当 $\Delta = 0$ 时：方程有两个相等的实数根
- 当 $\Delta < 0$ 时：方程没有实数根
"""

def fix_latex_format(text):
    """全面修复 LaTeX 格式：清理HTML、转换括号、修复命令"""
    if not text:
        return text
    
    # 1. 先清理 HTML 标签（防止之前渲染的 KaTeX 错误标签混入）
    text = re.sub(r'<span[^>]*katex-error[^>]*>.*?</span>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. 转换括号格式 - 使用正确的2个 $
    text = re.sub(r'\\\[(.*?)\\\]', lambda m: '$$' + m.group(1) + '$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', lambda m: '$' + m.group(1) + '$', text, flags=re.DOTALL)
    
    # 3. 修复 \frac 和 \sqrt 缺少花括号
    text = re.sub(r'\\frac\s+([^\s{]+?)\s+([^\s{]+?)(?=\s|$|[\u4e00-\u9fff,，。；：])', r'\\frac{\1}{\2}', text)
    text = re.sub(r'\\sqrt\s+([^\s{]+?)(?=\s|$|[\u4e00-\u9fff,，。；：])', r'\\sqrt{\1}', text)
    
    # 4. 修复 \left^2 / \right^2 等无效语法 → ^{2}
    text = re.sub(r'\\left\s*\^(\d+)', r'^{\1}', text)
    text = re.sub(r'\\right\s*\^(\d+)', r'^{\1}', text)
    
    # 5. 修复 \left\frac / \right\frac
    text = re.sub(r'\\left\s*\\frac', r'\\frac', text)
    text = re.sub(r'\\right\s*\\frac', r'\\frac', text)
    
    # 6. 修复 \left( / \right) 等
    text = re.sub(r'\\left\s*\(', '(', text)
    text = re.sub(r'\\right\s*\)', ')', text)
    text = re.sub(r'\\left\s*\[', '[', text)
    text = re.sub(r'\\right\s*\]', ']', text)
    
    # 7. 修复 \geq \leq 空格
    text = re.sub(r'\\geq(?![a-zA-Z{])', r' \\geq ', text)
    text = re.sub(r'\\leq(?![a-zA-Z{])', r' \\leq ', text)
    
    # 8. 清理多余空白 - 保留换行，只清理行内多余空格
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # 只清理每一行内的多余空格
        cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
        cleaned_lines.append(cleaned_line)
    text = '\n'.join(cleaned_lines)
    
    return text

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    original_text: Optional[str] = None
    structured_note: Optional[str] = None
    tags: Optional[str] = None
    folder: Optional[str] = None
    pdf_source: Optional[str] = None
    pdf_page: Optional[int] = None
    pdf_anchor: Optional[str] = None

class NoteCreate(BaseModel):
    text: str
    course_id: int = 1
    user_id: int = 1
    tags: list = []
    folder: Optional[str] = "默认笔记本"
    pdf_source: Optional[str] = None
    pdf_page: Optional[int] = None
    pdf_anchor: Optional[str] = None

@router.post("/upload")
async def upload_note(
    file: UploadFile = File(None),
    text: str = Form(None),
    course_id: int = Form(1),
    user_id: int = Form(1),
    custom_instruction: str = Form("")
):
    # ---- 诊断日志 ----
    print(f"[DEBUG] 收到 text 字段: {repr(text)}")
    print(f"[DEBUG] 收到 file 字段: {file.filename if file else None}")
    
    # ---- 修复：确保 original 不会是空 ----
    if file:
        original = f"[文件内容：{file.filename}]"
    elif text and text.strip():
        original = text.strip()
    else:
        raise HTTPException(status_code=400, detail="请提供文本或文件")
    
    print(f"[DEBUG] original 取值: {repr(original)}")
    
    # 文本预处理：过滤噪音
    original = re.sub(r'\s+', ' ', original).strip()
    if len(original) > 4000:
        original = original[:4000] + "...(文本过长已截断)"
    
    # 构建防模板 prompt
    custom_section = f"\n\n【特别要求】\n用户指定重点：{custom_instruction}\n" if custom_instruction.strip() else ""
    
    prompt = f"""你是一位专业的学习整理师。请根据以下课堂文本，生成三个部分，分别用代码块包裹。

【待整理文本】
{original}{custom_section}

【要求】
第一部分：结构化笔记（```markdown 代码块）
- 包含标题、分级要点、公式，禁止出现'[主题名称]'等占位符。

第二部分：10个问答闪卡（```json 代码块）
- 格式：[{{"question":"...","answer":"..."}}, ...]

第三部分：思维导图（```mindmap 代码块，也是JSON格式）
- 必须是一棵三层树形结构，反映知识的逻辑层次。
- 根节点是"笔记主题"（根据内容自拟）。
- 二级节点是主要章节或概念。
- 三级节点是各概念下的关键点、公式名称或具体例子。
- JSON格式示例：{{"name":"三角函数","children":[{{"name":"同角关系","children":[{{"name":"平方关系: sin²+cos²=1"}},{{"name":"商数关系: tan=sin/cos"}}]}},{{"name":"特殊角","children":[{{"name":"30°函数值"}},{{"name":"45°函数值"}}]}}]}}

直接输出三个代码块，不要额外解释。"""
    
    try:
        # 调用 AI
        ai_response = await chat_completion([
            {"role": "system", "content": latex_system},
            {"role": "user", "content": prompt}
        ])
        
        print(f"[DEBUG] AI 返回长度: {len(ai_response)} 字符")
        print(f"[DEBUG] AI 返回前200字: {ai_response[:200]}")
        
        # Markdown 解析：兼容无代码块的情况
        md_match = re.search(r'```(?:markdown)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        if md_match:
            structured = md_match.group(1).strip()
        else:
            structured = ai_response[:500] if len(ai_response) > 500 else ai_response
        
        # 强制修复 LaTeX 格式
        structured = fix_latex_format(structured)
        
        # 兜底：如果笔记太短或充满模板词，直接用原文
        placeholder_patterns = ['[主题名称]', '[目标描述]', '[定义]', '[答案]', '[问题]']
        if len(structured) < 50 or any(placeholder in structured for placeholder in placeholder_patterns):
            print(f"[DEBUG] 检测到模板占位符，使用原文作为笔记")
            structured = f"# 原始笔记\n\n{original}"
        
        # JSON 解析：处理格式错误
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        flashcard_data = []
        if json_match:
            try:
                flashcard_data = json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                import ast
                try:
                    flashcard_data = ast.literal_eval(json_match.group(1).strip())
                except:
                    flashcard_data = []
        
        # 如果解析后为空，生成兜底闪卡
        if not flashcard_data:
            print(f"[DEBUG] 闪卡解析为空，生成兜底闪卡")
            fallback_q = original[:30] + "..." if len(original) > 30 else original
            flashcard_data = [{"question": f"请总结'{fallback_q}'的核心内容", "answer": original[:200]}]
        
        # ----- 解析思维导图 -----
        mindmap_data = {"name": "课堂笔记", "children": []}
        mindmap_match = re.search(r'```(?:mindmap)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        if mindmap_match:
            try:
                parsed = json.loads(mindmap_match.group(1).strip())
                if "name" in parsed and "children" in parsed:
                    mindmap_data = parsed
            except:
                pass
        mindmap = json.dumps(mindmap_data)
        
        print(f"[DEBUG] 最终生成闪卡数量: {len(flashcard_data)}")
        
    except Exception as e:
        print(f"[ERROR] AI 调用失败: {str(e)}")
        # AI 调用失败时使用兜底方案
        structured = f"# 原始笔记\n\n{original}"
        flashcard_data = [
            {"question": f"问题 {i+1}", "answer": f"答案 {i+1}"}
            for i in range(5)
        ]
        # 兜底思维导图
        mindmap_data = {"name": "课堂笔记", "children": [{"name": item.get("question", "知识点")} for item in flashcard_data]}
        mindmap = json.dumps(mindmap_data)
    
    db = SessionLocal()
    note = Note(
        user_id=user_id, course_id=course_id,
        original_text=original, structured_note=structured,
        mindmap_json=mindmap
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    for item in flashcard_data:
        fc = Flashcard(
            note_id=note.id, user_id=user_id, course_id=course_id,
            question=item["question"], answer=item["answer"],
            next_review_date=datetime.datetime.now()
        )
        db.add(fc)
    db.commit()
    db.close()
    return note

class NoteCreateDirect(BaseModel):
    title: Optional[str] = None
    content: str
    course_id: int = 1
    user_id: int = 1
    tags: list = []
    folder: Optional[str] = "默认笔记本"
    pdf_source: Optional[str] = None
    pdf_page: Optional[int] = None
    pdf_anchor: Optional[str] = None

@router.post("/upload-json")
async def upload_note_json(note: NoteCreate):
    original = note.text.strip() if note.text.strip() else "[无内容]"
    
    # 文本预处理
    original = re.sub(r'\s+', ' ', original).strip()
    if len(original) > 4000:
        original = original[:4000] + "...(文本过长已截断)"
    
    prompt = f"""你是一位专业的学习整理师。请根据以下课堂文本，生成三个部分，分别用代码块包裹。
    
【待整理文本】
{original}

【要求】
第一部分：结构化笔记（```markdown 代码块）
- 包含标题、分级要点、公式，禁止出现'[主题名称]'等占位符。

第二部分：10个问答闪卡（```json 代码块）
- 格式：[{{"question":"...","answer":"...", ...}}]

第三部分：思维导图（```mindmap 代码块，也是JSON格式）
- 必须是一棵三层树形结构，反映知识的逻辑层次。
- 根节点是"笔记主题"（根据内容自拟）。
- 二级节点是主要章节或概念。
- 三级节点是各概念下的关键点、公式名称或具体例子。
- JSON格式示例：{{"name":"三角函数","children":[{{"name":"同角关系","children":[{{"name":"平方关系: sin²+cos²=1"}}]}}]}}

直接输出三个代码块，不要额外解释。"""
    
    try:
        ai_response = await chat_completion([
            {"role": "system", "content": latex_system},
            {"role": "user", "content": prompt}
        ])
        
        md_match = re.search(r'```(?:markdown)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        structured = md_match.group(1).strip() if md_match else ai_response[:500]
        
        # 强制修复 LaTeX 格式
        structured = fix_latex_format(structured)
        
        if len(structured) < 50 or any(ph in structured for ph in ['[主题名称]', '[目标描述]', '[定义]']):
            structured = f"# 原始笔记\n\n{original}"
        
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        flashcard_data = []
        if json_match:
            try:
                flashcard_data = json.loads(json_match.group(1).strip())
            except:
                import ast
                try:
                    flashcard_data = ast.literal_eval(json_match.group(1).strip())
                except:
                    flashcard_data = []
        
        if not flashcard_data:
            flashcard_data = [{"question": f"请总结\"{original[:30]}...\"的核心内容", "answer": original[:200]}]
        
        # ----- 解析思维导图 -----
        mindmap_data = {"name": "课堂笔记", "children": []}
        mindmap_match = re.search(r'```(?:mindmap)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        if mindmap_match:
            try:
                parsed = json.loads(mindmap_match.group(1).strip())
                if "name" in parsed and "children" in parsed:
                    mindmap_data = parsed
            except:
                pass
        mindmap = json.dumps(mindmap_data)
        
    except Exception as e:
        structured = f"# 原始笔记\n\n{original}"
        flashcard_data = [{"question": f"问题 {i+1}", "answer": f"答案 {i+1}"} for i in range(5)]
        # 兜底思维导图
        mindmap_data = {"name": "课堂笔记", "children": [{"name": item.get("question", "知识点")} for item in flashcard_data]}
        mindmap = json.dumps(mindmap_data)
    
    tags_str = ",".join(note.tags) if note.tags else ""
    
    db = SessionLocal()
    new_note = Note(
        user_id=note.user_id, course_id=note.course_id,
        original_text=original, structured_note=structured,
        mindmap_json=mindmap,
        tags=tags_str,
        folder=note.folder or "默认笔记本"
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    
    for item in flashcard_data:
        fc = Flashcard(
            note_id=new_note.id, user_id=note.user_id, course_id=note.course_id,
            question=item["question"], answer=item["answer"],
            next_review_date=datetime.datetime.now()
        )
        db.add(fc)
    db.commit()
    db.close()
    return new_note

@router.post("/")
async def create_note_direct(note: NoteCreateDirect):
    """直接创建笔记，不经过 AI 处理"""
    db = SessionLocal()
    
    # 准备内容
    original = note.content.strip() if note.content.strip() else "[无内容]"
    title = note.title.strip() if note.title else ""
    
    # 如果没有标题，尝试从内容中提取
    if not title:
        match = re.search(r'^#\s+(.+)$', original, re.MULTILINE)
        if match:
            title = match.group(1).strip()
        else:
            first_line = original.split('\n')[0]
            title = first_line[:50] if first_line else "未命名笔记"
    
    # 格式化结构化内容
    structured = original
    if not structured.startswith('#'):
        structured = f"# {title}\n\n{original}"
    
    # 强制修复 LaTeX 格式
    structured = fix_latex_format(structured)
    
    tags_str = ",".join(note.tags) if note.tags else ""
    
    # 创建笔记
    new_note = Note(
        user_id=note.user_id,
        course_id=note.course_id,
        title=title,
        original_text=original,
        structured_note=structured,
        mindmap_json=json.dumps({"name": title, "children": []}),
        tags=tags_str,
        folder=note.folder or "默认笔记本",
        pdf_source=note.pdf_source,
        pdf_page=note.pdf_page,
        pdf_anchor=note.pdf_anchor
    )
    
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    
    # 【新增】：提取并保存双向链接
    linked_titles = re.findall(r'\[\[(.*?)\]\]', structured)
    for linked_title in set(linked_titles):
        db.execute(text("INSERT INTO note_links (source_id, target_title) VALUES (:sid, :title)"), 
                {"sid": new_note.id, "title": linked_title.strip()})
    db.commit()
    
    db.close()
    
    return new_note

class NoteImportItem(BaseModel):
    title: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[str] = None
    course_id: Optional[int] = None
    original_text: Optional[str] = None
    structured_note: Optional[str] = None
    created_at: Optional[str] = None
    pdf_source: Optional[str] = None
    pdf_page: Optional[int] = None
    pdf_anchor: Optional[str] = None

class ImportNotesRequest(BaseModel):
    notes: list[NoteImportItem]

@router.post("/import")
async def import_notes(request: ImportNotesRequest):
    """批量导入笔记"""
    db = SessionLocal()
    imported_count = 0
    
    for note_data in request.notes:
        try:
            title = note_data.title.strip() if note_data.title else "未命名笔记"
            original = note_data.original_text or note_data.structured_note or "[无内容]"
            structured = note_data.structured_note or original
            
            if not structured.startswith('#'):
                structured = f"# {title}\n\n{structured}"
            
            tags_str = note_data.tags or ""
            
            new_note = Note(
                user_id=1,
                course_id=note_data.course_id,
                title=title,
                original_text=original,
                structured_note=structured,
                mindmap_json=json.dumps({"name": title, "children": []}),
                tags=tags_str,
                folder=note_data.folder or "默认笔记本",
                pdf_source=note_data.pdf_source or "",
                pdf_page=note_data.pdf_page,
                pdf_anchor=note_data.pdf_anchor
            )
            
            db.add(new_note)
            db.commit()
            imported_count += 1
        except Exception as e:
            print(f"导入笔记时出错: {str(e)}")
            db.rollback()
            continue
    
    db.close()
    return {"imported": imported_count, "total": len(request.notes)}

@router.get("/list")
def get_notes(course_id: Optional[int] = None, user_id: int = 1):
    db = SessionLocal()
    # 如果提供了 course_id，则只返回该课程的笔记；否则返回所有笔记
    query = db.query(Note).filter(Note.user_id == user_id)
    if course_id is not None:
        query = query.filter(Note.course_id == course_id)
    notes = query.order_by(Note.id.desc()).all()
    result = []
    for note in notes:
        note_dict = {
            "id": note.id,
            "user_id": note.user_id,
            "course_id": note.course_id,
            "title": note.title,
            "original_text": note.original_text,
            "structured_note": note.structured_note,
            "mindmap_json": note.mindmap_json,
            "tags": note.tags,
            "folder": note.folder or "默认笔记本",
            "pdf_source": note.pdf_source,
            "pdf_page": note.pdf_page,
            "pdf_anchor": note.pdf_anchor,
            "created_at": note.created_at.isoformat()
        }
        result.append(note_dict)
    db.close()
    return result

@router.get("/search")
def search_notes(keyword: str, course_id: int = 1, user_id: int = 1):
    """全局模糊搜索接口 - 同时搜索标题和内容"""
    db = SessionLocal()
    if not keyword.strip():
        db.close()
        return {"success": True, "data": []}
    
    # 使用 or_ 同时在标题和内容中进行模糊查询 (LIKE %keyword%)
    results = db.query(Note).filter(
        Note.user_id == user_id,
        or_(
            Note.title.ilike(f"%{keyword}%"),
            Note.original_text.ilike(f"%{keyword}%"),
            Note.structured_note.ilike(f"%{keyword}%")
        )
    ).all()
    
    result = []
    for note in results:
        note_dict = {
            "id": note.id,
            "user_id": note.user_id,
            "course_id": note.course_id,
            "title": note.title,
            "original_text": note.original_text,
            "structured_note": note.structured_note,
            "mindmap_json": note.mindmap_json,
            "tags": note.tags,
            "folder": note.folder or "默认笔记本",
            "created_at": note.created_at.isoformat()
        }
        result.append(note_dict)
    db.close()
    return {"success": True, "data": result}

@router.delete("/{note_id}")
def delete_note(note_id: int, user_id: int = 1):
    db = SessionLocal()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        db.close()
        raise HTTPException(status_code=404, detail="笔记不存在")
    db.query(Flashcard).filter(Flashcard.note_id == note_id).delete()
    db.delete(note)
    db.commit()
    db.close()
    return {"message": "已删除"}

@router.post("/{note_id}/regenerate")
async def regenerate_note(note_id: int, user_id: int = 1):
    """重新生成笔记内容（含结构化笔记、闪卡和思维导图）"""
    db = SessionLocal()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        db.close()
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    original = note.original_text
    if not original or original.strip() == "":
        original = "[重新生成的笔记]"
    
    # 文本预处理
    original = re.sub(r'\s+', ' ', original).strip()
    if len(original) > 4000:
        original = original[:4000] + "...(文本过长已截断)"
    
    user_prompt = f"""请帮我深度整理并美化这份课堂笔记，要求格式完美、LaTeX 公式规范：

【原始笔记内容】
{original}

【输出格式】
请生成三个部分，分别用代码块包裹：

第一部分：结构化笔记（```markdown 代码块）
- 使用标准 Markdown 格式
- 所有数学公式必须使用正确的 LaTeX 语法

第二部分：10个问答闪卡（```json 代码块）
- 格式：[{{"question":"...","answer":"..."}}...]

第三部分：思维导图（```mindmap 代码块）
- JSON 格式的三层树形结构
- 示例：{{"name":"笔记主题","children":[{{"name":"章节1","children":[{{"name":"知识点1"}}]}}]}}

直接输出，不要额外解释。"""

    try:
        # 调用 AI：使用全局规范 system prompt
        ai_response = await chat_completion([
            {"role": "system", "content": latex_system},
            {"role": "user", "content": user_prompt}
        ])
        
        # Markdown 解析
        md_match = re.search(r'```(?:markdown)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        if md_match:
            structured = md_match.group(1).strip()
        else:
            structured = ai_response[:500] if len(ai_response) > 500 else ai_response
        
        # 兜底检查
        placeholder_patterns = ['[主题名称]', '[目标描述]', '[定义]', '[答案]', '[问题]']
        if len(structured) < 50 or any(placeholder in structured for placeholder in placeholder_patterns):
            structured = f"# 原始笔记\n\n{original}"
        
        # JSON 解析闪卡
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        flashcard_data = []
        if json_match:
            try:
                flashcard_data = json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                    import ast
                    try:
                        flashcard_data = ast.literal_eval(json_match.group(1).strip())
                    except:
                        flashcard_data = []
        
        if not flashcard_data:
            fallback_q = original[:30] + "..." if len(original) > 30 else original
            flashcard_data = [{"question": f"请总结'{fallback_q}'的核心内容", "answer": original[:200]}]
        
        # 解析思维导图
        mindmap_data = {"name": "课堂笔记", "children": []}
        mindmap_match = re.search(r'```(?:mindmap)?\s*\n?(.*?)```', ai_response, re.DOTALL | re.IGNORECASE)
        if mindmap_match:
            try:
                parsed = json.loads(mindmap_match.group(1).strip())
                if "name" in parsed and "children" in parsed:
                    mindmap_data = parsed
            except:
                pass
        mindmap = json.dumps(mindmap_data)
        
    except Exception as e:
        # AI 调用失败时使用兜底方案
        print(f"[ERROR] AI 调用失败: {str(e)}")
        structured = f"# 原始笔记\n\n{original}"
        flashcard_data = [{"question": f"问题 {i+1}", "answer": f"答案 {i+1}"} for i in range(5)]
        mindmap_data = {"name": "课堂笔记", "children": [{"name": item.get("question", "知识点")} for item in flashcard_data]}
        mindmap = json.dumps(mindmap_data)
    
    # 【核心修复】：强制修复 LaTeX 格式
    structured = fix_latex_format(structured)
    
    # 更新笔记内容
    note.structured_note = structured
    note.mindmap_json = mindmap
    
    # 删除旧闪卡，插入新闪卡
    db.query(Flashcard).filter(Flashcard.note_id == note_id).delete()
    
    for item in flashcard_data:
        fc = Flashcard(
            note_id=note.id, user_id=note.user_id, course_id=note.course_id,
            question=item["question"], answer=item["answer"],
            next_review_date=datetime.datetime.now()
        )
        db.add(fc)
    
    db.commit()
    db.refresh(note)
    
    result = {
        "success": True,
        "message": "重构成功",
        "data": {
            "content": structured,
            "mindmap": mindmap
        }
    }
    db.close()
    return result

@router.put("/{note_id}")
def update_note(note_id: int, note_update: NoteUpdate, user_id: int = 1):
    db = SessionLocal()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        db.close()
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    try:
        if note_update.title is not None:
            note.title = note_update.title
        if note_update.original_text is not None:
            note.original_text = note_update.original_text
        if note_update.structured_note is not None:
            # 修复 LaTeX 格式
            note.structured_note = fix_latex_format(note_update.structured_note)
            # 【新增】：提取并更新双向链接
            linked_titles = re.findall(r'\[\[(.*?)\]\]', note.structured_note)
            # 清理这篇笔记旧的连接
            db.execute(text("DELETE FROM note_links WHERE source_id = :sid"), {"sid": note_id})
            # 注入新的突触连接
            for title in set(linked_titles):
                db.execute(text("INSERT INTO note_links (source_id, target_title) VALUES (:sid, :title)"), 
                        {"sid": note_id, "title": title.strip()})
        if note_update.tags is not None:
            note.tags = note_update.tags
        if note_update.folder is not None:
            note.folder = note_update.folder
        if note_update.pdf_source is not None:
            note.pdf_source = note_update.pdf_source
        if note_update.pdf_page is not None:
            note.pdf_page = note_update.pdf_page
        if note_update.pdf_anchor is not None:
            note.pdf_anchor = note_update.pdf_anchor
        db.commit()
        db.refresh(note)
        db.close()
        return {"success": True, "message": "保存成功", "data": {"title": note.title, "tags": note.tags, "folder": note.folder, "pdf_source": note.pdf_source, "pdf_page": note.pdf_page, "pdf_anchor": note.pdf_anchor}}
    except Exception as e:
        db.rollback()
        db.close()
        return {"error": True, "message": str(e)}

@router.get("/flashcards/review")
def get_today_flashcards(course_id: int = 1, user_id: int = 1):
    db = SessionLocal()
    today = datetime.date.today()
    cards = db.query(Flashcard).filter(
        Flashcard.user_id == user_id,
        Flashcard.course_id == course_id,
        Flashcard.next_review_date <= today
    ).all()
    result = []
    for card in cards:
        result.append({
            "id": card.id,
            "question": card.question,
            "answer": card.answer,
            "ease_factor": card.ease_factor,
            "interval": card.interval,
            "next_review_date": card.next_review_date.isoformat()
        })
    db.close()
    return result

@router.get("/links")
async def get_all_links():
    """获取全库所有的双向链接数据"""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT source_id, target_title FROM note_links")).fetchall()
        links = [{"source_id": row[0], "target_title": row[1]} for row in result]
        return {"success": True, "data": links}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()

# ================= 闪卡引擎接口 =================

class FlashcardCreate(BaseModel):
    note_id: int
    question: str
    answer: str

class AIAnswerRequest(BaseModel):
    question: str
    context: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{note_id}/flashcards")
async def create_flashcard(note_id: int, card: FlashcardCreate, db: SessionLocal = Depends(get_db)):
    """保存闪卡到数据库"""
    try:
        # 先获取笔记信息
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            return {"success": False, "message": "笔记不存在"}
        
        # 创建闪卡对象
        flashcard = Flashcard(
            note_id=note_id,
            user_id=note.user_id,
            course_id=note.course_id,
            question=card.question,
            answer=card.answer,
            next_review_date=datetime.datetime.now()
        )
        db.add(flashcard)
        db.commit()
        db.refresh(flashcard)
        return {"success": True, "message": "闪卡制作成功"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.post("/ai/generate-flashcard")
async def generate_flashcard_answer(req: AIAnswerRequest):
  """调用 DeepSeek API 生成闪卡答案（和备考计划同方式）"""
  prompt = f"你是一个专业的学习助手。请根据以下笔记内容，为知识点/问题提取或生成极其精简的答案，适合用于记忆闪卡背面。\n笔记内容：{req.context}\n问题：{req.question}\n请直接输出答案，不要废话。"
  
  try:
    messages = [{"role": "user", "content": prompt}]
    ai_response = await chat_completion(messages, temperature=0.3, max_tokens=500)
    return {"success": True, "answer": ai_response.strip()}
  except Exception as e:
    return {"success": False, "message": str(e)}

@router.get("/flashcards")
async def get_all_flashcards():
    """获取所有闪卡列表"""
    db = SessionLocal()
    try:
        # 使用 ORM 查询
        flashcards_query = db.query(Flashcard, Note).join(Note, Flashcard.note_id == Note.id).order_by(Flashcard.id.desc()).all()
        flashcards = [
            {
                "id": fc.id,
                "note_id": fc.note_id,
                "front": fc.question,  # 映射 question 到 front
                "back": fc.answer,     # 映射 answer 到 back
                "created_at": None,
                "note_title": n.title if n else "未知笔记"
            }
            for fc, n in flashcards_query
        ]
        return {"success": True, "data": flashcards}
    except Exception as e:
        print(f"[ERROR] 获取闪卡失败: {str(e)}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()

@router.delete("/flashcards/{card_id}")
async def delete_flashcard(card_id: int):
    """删除指定闪卡"""
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM flashcards WHERE id = :cid"), {"cid": card_id})
        db.commit()
        return {"success": True, "message": "闪卡已删除"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()

# ================= 文件夹移动接口 =================
class FolderMoveRequest(BaseModel):
    source_path: str
    target_path: str

@router.post("/move-folder")
async def move_folder(req: FolderMoveRequest, user_id: int = 1):
    """移动文件夹：将 source_path 下的所有笔记和子文件夹移动到 target_path/source_path，target_path 为空表示移到根目录"""
    db = SessionLocal()
    try:
        source_path = req.source_path
        target_path = req.target_path
        
        # 获取源文件夹的最后一个部分作为文件夹名称
        source_folder_name = source_path.split('/')[-1]
        
        # 目标文件夹完整路径：如果 target_path 为空，表示直接移到根目录
        if not target_path or target_path.strip() == '':
            full_target_path = source_folder_name
        else:
            full_target_path = f"{target_path}/{source_folder_name}"
        
        # 查找所有在源文件夹下的笔记（包括子文件夹）
        notes_to_move = db.query(Note).filter(
            Note.user_id == user_id,
            Note.folder.like(f"{source_path}/%") | (Note.folder == source_path)
        ).all()
        
        # 批量更新文件夹路径
        for note in notes_to_move:
            # 将 note.folder 中的 source_path 替换为 full_target_path
            if note.folder == source_path:
                note.folder = full_target_path
            else:
                # 处理子文件夹：source_path/subfolder → full_target_path/subfolder
                relative_path = note.folder[len(source_path) + 1:]
                note.folder = f"{full_target_path}/{relative_path}"
        
        db.commit()
        return {
            "success": True, 
            "message": f"文件夹移动成功，共移动 {len(notes_to_move)} 个笔记",
            "data": {"moved_count": len(notes_to_move)}
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()