from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import SessionLocal
from models import Literature
import os
import uuid

router = APIRouter()

LITERATURE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'literature')
if not os.path.exists(LITERATURE_DIR):
    os.makedirs(LITERATURE_DIR)

@router.post("/upload")
async def upload_literature(file: UploadFile = File(...), category_id: str = Form(None)):
    ext = os.path.splitext(file.filename)[1]
    if ext.lower() != '.pdf':
        return {"error": "只支持 PDF 文件"}
    
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(LITERATURE_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(await file.read())
    
    db = SessionLocal()
    try:
        new_doc = Literature(
            name=os.path.splitext(file.filename)[0],
            filename=filename,
            filepath=filepath,
            category_id=category_id
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        return {
            "success": True,
            "data": {
                "id": new_doc.id,
                "name": new_doc.name,
                "filename": new_doc.filename,
                "url": f"/api/literature/files/{new_doc.filename}",
                "category_id": new_doc.category_id
            }
        }
    except Exception as e:
        db.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        return {"error": True, "message": str(e)}
    finally:
        db.close()

@router.get("/files/{filename}")
async def get_literature_file(filename: str):
    filepath = os.path.join(LITERATURE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, media_type="application/pdf")

@router.get("/list")
async def get_literature_list():
    db = SessionLocal()
    try:
        docs = db.query(Literature).all()
        return {
            "success": True,
            "data": [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "filename": doc.filename,
                    "url": f"/api/literature/files/{doc.filename}",
                    "category_id": doc.category_id
                }
                for doc in docs
            ]
        }
    except Exception as e:
        return {"error": True, "message": str(e)}
    finally:
        db.close()

@router.put("/{doc_id}/category")
async def update_category(doc_id: int, category_id: str = Form(None)):
    db = SessionLocal()
    try:
        doc = db.query(Literature).filter(Literature.id == doc_id).first()
        if not doc:
            return {"error": True, "message": "文献不存在"}
        doc.category_id = category_id
        db.commit()
        return {"success": True, "message": "更新成功"}
    except Exception as e:
        db.rollback()
        return {"error": True, "message": str(e)}
    finally:
        db.close()

@router.delete("/{doc_id}")
async def delete_literature(doc_id: int):
    db = SessionLocal()
    try:
        doc = db.query(Literature).filter(Literature.id == doc_id).first()
        if not doc:
            return {"error": True, "message": "文献不存在"}
        
        if doc.filepath and os.path.exists(doc.filepath):
            os.remove(doc.filepath)
        
        db.delete(doc)
        db.commit()
        return {"success": True, "message": "删除成功"}
    except Exception as e:
        db.rollback()
        return {"error": True, "message": str(e)}
    finally:
        db.close()