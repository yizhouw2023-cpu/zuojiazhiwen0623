"""Word cloud serving and export endpoints."""
from __future__ import annotations
import os
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, FileResponse
from PIL import Image

from app.core.wordcloud_gen import generate_wordcloud, wordcloud_to_bytes

router = APIRouter(prefix="/api", tags=["wordcloud"])

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
WORDCLOUDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wordclouds")


def _load_word_freq(session_id: str) -> dict[str, int]:
    """Load word frequency dict from saved analysis JSON."""
    analysis_path = os.path.join(UPLOADS_DIR, session_id, "analysis.json")
    if not os.path.exists(analysis_path):
        raise HTTPException(status_code=404, detail="未找到分析结果，请先运行分析")
    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("word_freq", {}), data.get("author_name", "")


@router.get("/wordcloud/{session_id}/{author}")
async def serve_wordcloud(
    session_id: str,
    author: str,
    w: int = Query(300, alias="w"),
    h: int = Query(200, alias="h"),
):
    """Serve a word cloud PNG image. Supports resizing via w/h query params."""
    # Validate session_id to prevent path traversal
    if ".." in session_id or "/" in session_id or "\\" in session_id:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    word_freq, author_name = _load_word_freq(session_id)

    # Check cache
    cache_key = f"{session_id}_{author}_{w}x{h}"
    cache_path = os.path.join(WORDCLOUDS_DIR, f"{cache_key}.png")

    if os.path.exists(cache_path):
        return FileResponse(cache_path, media_type="image/png")

    # Generate word cloud
    image = generate_wordcloud(word_freq, author_name, width=w, height=h)
    if image is None:
        raise HTTPException(status_code=500, detail="词云生成失败，请确认词云依赖已安装")

    # Save to cache
    image.save(cache_path, "PNG")

    # Return as bytes
    img_bytes = wordcloud_to_bytes(image, "PNG")
    return Response(content=img_bytes, media_type="image/png")


@router.get("/export/wordcloud/{session_id}/{author}")
async def export_wordcloud(
    session_id: str,
    author: str,
    format: str = Query("png", alias="format"),
):
    """Download the full-size (600x400) word cloud image."""
    if ".." in session_id or "/" in session_id or "\\" in session_id:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    word_freq, author_name = _load_word_freq(session_id)

    image = generate_wordcloud(word_freq, author_name, width=600, height=400)
    if image is None:
        raise HTTPException(status_code=500, detail="词云生成失败")

    fmt = format.upper()
    if fmt in ("JPG", "JPEG"):
        img_bytes = wordcloud_to_bytes(image, "JPEG")
        media_type = "image/jpeg"
        ext = "jpg"
    else:
        img_bytes = wordcloud_to_bytes(image, "PNG")
        media_type = "image/png"
        ext = "png"

    filename = f"{author_name}_词云图.{ext}"
    return Response(
        content=img_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
