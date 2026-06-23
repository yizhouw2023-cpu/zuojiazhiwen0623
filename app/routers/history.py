"""History CRUD endpoints."""
from __future__ import annotations
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.history import HistoryEntry


class SaveHistoryRequest(BaseModel):
    author_a: str = ""
    author_b: str = ""
    result_a_json: str = ""
    result_b_json: str = ""
    comparison_json: str = ""
    appreciation_text: str = ""


router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
async def list_history(db: Session = Depends(get_db)):
    """List all history entries (newest first)."""
    result = db.execute(
        select(HistoryEntry).order_by(HistoryEntry.id.desc())
    )
    entries = result.scalars().all()
    return [
        {
            "id": e.id,
            "author_a": e.author_a,
            "author_b": e.author_b,
            "timestamp": e.timestamp,
            "appreciation_text": e.appreciation_text,
            "created_at": e.created_at,
        }
        for e in entries
    ]


@router.get("/history/{entry_id}")
async def get_history(entry_id: int, db: Session = Depends(get_db)):
    """Retrieve a full history entry with results."""
    result = db.execute(select(HistoryEntry).where(HistoryEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="未找到该历史记录")

    data = entry.to_dict()
    # Parse JSON fields
    try:
        data["result_a"] = json.loads(data["result_a_json"])
        data["result_b"] = json.loads(data["result_b_json"])
        data["comparison"] = json.loads(data["comparison_json"])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="历史记录数据损坏")

    return data


@router.post("/history")
async def save_history(
    req: SaveHistoryRequest,
    db: Session = Depends(get_db),
):
    """Save a new history entry. Auto-trims to max 50 entries."""
    entry = HistoryEntry(
        author_a=req.author_a,
        author_b=req.author_b,
        timestamp=datetime.now().isoformat(),
        result_a_json=req.result_a_json,
        result_b_json=req.result_b_json,
        comparison_json=req.comparison_json,
        appreciation_text=req.appreciation_text,
        created_at=datetime.now().isoformat(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Enforce max 50 entries
    count_result = db.execute(select(func.count(HistoryEntry.id)))
    total = count_result.scalar()
    if total > 50:
        # Delete oldest entries beyond 50
        oldest = db.execute(
            select(HistoryEntry.id).order_by(HistoryEntry.id.asc()).limit(total - 50)
        )
        ids_to_delete = [row[0] for row in oldest.all()]
        if ids_to_delete:
            db.execute(delete(HistoryEntry).where(HistoryEntry.id.in_(ids_to_delete)))
            db.commit()

    return {"id": entry.id, "ok": True}


@router.delete("/history/{entry_id}")
async def delete_history(entry_id: int, db: Session = Depends(get_db)):
    """Delete a single history entry."""
    result = db.execute(select(HistoryEntry).where(HistoryEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="未找到该历史记录")
    db.delete(entry)
    db.commit()
    return {"ok": True}


@router.delete("/history")
async def clear_history(db: Session = Depends(get_db)):
    """Delete all history entries."""
    db.execute(delete(HistoryEntry))
    db.commit()
    return {"ok": True}
