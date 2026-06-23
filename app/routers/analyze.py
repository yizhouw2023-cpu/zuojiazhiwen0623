"""Analysis endpoint — orchestrates file reading + NLP analysis."""
from __future__ import annotations
import os
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.reader import read_file
from app.core.text_utils import DEFAULT_STOPWORDS
from app.core.analyzer import analyze_text, compare_results

router = APIRouter(prefix="/api", tags=["analyze"])

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


class AnalyzeRequest(BaseModel):
    session_id_a: str
    session_id_b: str
    author_a: str = "作家A"
    author_b: str = "作家B"
    use_default_stopwords: bool = True
    custom_stopwords: str = ""  # comma or space separated


@router.post("/analyze")
async def run_analysis(req: AnalyzeRequest):
    """Run NLP analysis on two uploaded text files."""
    # Build stop words set
    stop_words: set[str] = set()
    if req.use_default_stopwords:
        stop_words.update(DEFAULT_STOPWORDS)
    if req.custom_stopwords.strip():
        import re
        words = re.split(r'[,，\s]+', req.custom_stopwords.strip())
        stop_words.update(w for w in words if w.strip())

    # Read files
    filepath_a = os.path.join(UPLOADS_DIR, req.session_id_a, "text_A.txt")
    filepath_b = os.path.join(UPLOADS_DIR, req.session_id_b, "text_B.txt")

    # Also check for .docx
    for ext in [".docx", ".txt"]:
        if os.path.exists(os.path.join(UPLOADS_DIR, req.session_id_a, f"text_A{ext}")):
            filepath_a = os.path.join(UPLOADS_DIR, req.session_id_a, f"text_A{ext}")
        if os.path.exists(os.path.join(UPLOADS_DIR, req.session_id_b, f"text_B{ext}")):
            filepath_b = os.path.join(UPLOADS_DIR, req.session_id_b, f"text_B{ext}")

    try:
        text_a = read_file(filepath_a)
        text_b = read_file(filepath_b)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件读取失败: {e}")

    # Run analysis (these are CPU-bound, run synchronously for now)
    try:
        result_a = analyze_text(text_a, stop_words, author_name=req.author_a)
        result_b = analyze_text(text_b, stop_words, author_name=req.author_b)
        comparison = compare_results(result_a, result_b)
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"缺少依赖库: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {e}")

    # Save analysis results next to uploaded files for word cloud generation later
    for sid, result in [(req.session_id_a, result_a), (req.session_id_b, result_b)]:
        analysis_path = os.path.join(UPLOADS_DIR, sid, "analysis.json")
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False)

    return {
        "result_a": result_a.to_dict(),
        "result_b": result_b.to_dict(),
        "comparison": comparison.to_dict(),
        "text_a_sample": text_a[:2000],
        "text_b_sample": text_b[:2000],
    }
