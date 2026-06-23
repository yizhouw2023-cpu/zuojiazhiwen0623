"""File upload endpoint."""
from __future__ import annotations
import os
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

router = APIRouter(prefix="/api", tags=["upload"])

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_EXTENSIONS = {".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), author: str = Form("A")):
    """Upload a .txt or .docx file and return a session_id for later analysis."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}（仅支持 .txt / .docx）")

    # Create session dir
    session_id = uuid.uuid4().hex
    session_dir = os.path.join(UPLOADS_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Save file with original extension
    safe_name = f"text_{author}{ext}"
    filepath = os.path.join(session_dir, safe_name)

    try:
        with open(filepath, "wb") as f:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                shutil.rmtree(session_dir)
                raise HTTPException(status_code=400, detail="文件过大，最大支持 10MB")
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    return {
        "session_id": session_id,
        "filename": file.filename,
        "author_label": author,
    }
