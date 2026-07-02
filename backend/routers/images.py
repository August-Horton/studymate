from fastapi import APIRouter, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uuid

router = APIRouter()

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images')
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return {"error": "不支持的图片格式"}
    
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(await file.read())
    
    return {"success": True, "url": f"/api/images/{filename}"}

@router.get("/{filename}")
async def get_image(filename: str):
    filepath = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": "图片不存在"}
    return FileResponse(filepath)