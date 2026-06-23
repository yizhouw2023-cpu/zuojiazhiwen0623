"""Article appreciation endpoint — calls DeepSeek API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.deepseek import generate_appreciation
from app.config import settings

router = APIRouter(prefix="/api", tags=["appreciation"])


class AppreciationRequest(BaseModel):
    result_a: dict
    result_b: dict
    comparison: dict
    text_a_sample: str = ""
    text_b_sample: str = ""
    api_key: str = ""  # optional override from UI


@router.post("/appreciation")
async def create_appreciation(req: AppreciationRequest):
    """Generate a comparative literary commentary via DeepSeek API."""
    api_key = req.api_key.strip() or settings.deepseek_api_key

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="未配置 DeepSeek API Key。请在页面右上角设置中填入，或设置环境变量 DEEPSEEK_API_KEY。",
        )

    try:
        content = await generate_appreciation(
            result_a_json=req.result_a,
            result_b_json=req.result_b,
            comparison_json=req.comparison,
            text_a_sample=req.text_a_sample,
            text_b_sample=req.text_b_sample,
            api_key=api_key,
        )
        return {"content": content}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            raise HTTPException(status_code=401, detail="API Key 无效或无权访问，请检查后重试。")
        if "429" in error_msg:
            raise HTTPException(status_code=429, detail="API 请求过于频繁，请稍后重试。")
        if "timeout" in error_msg.lower():
            raise HTTPException(status_code=504, detail="API 请求超时，请稍后重试。")
        raise HTTPException(status_code=500, detail=f"赏析生成失败: {error_msg}")
