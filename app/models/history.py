"""SQLAlchemy ORM model for history entries."""
from __future__ import annotations
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class HistoryEntry(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_a = Column(String(256), nullable=False)
    author_b = Column(String(256), nullable=False)
    timestamp = Column(String(64), nullable=False)
    result_a_json = Column(Text, nullable=False)
    result_b_json = Column(Text, nullable=False)
    comparison_json = Column(Text, nullable=False)
    appreciation_text = Column(Text, nullable=True)
    created_at = Column(String(64), nullable=False, default=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author_a": self.author_a,
            "author_b": self.author_b,
            "timestamp": self.timestamp,
            "result_a_json": self.result_a_json,
            "result_b_json": self.result_b_json,
            "comparison_json": self.comparison_json,
            "appreciation_text": self.appreciation_text,
            "created_at": self.created_at,
        }
