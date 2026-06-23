"""Data classes for analysis and comparison results."""
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class AnalysisResult:
    author_name: str = ""
    total_words: int = 0
    total_sentences: int = 0
    avg_sentence_length: float = 0.0
    top_words: list = None
    word_freq: dict = None
    unique_content_words: int = 0

    def __post_init__(self):
        if self.top_words is None:
            self.top_words = []
        if self.word_freq is None:
            self.word_freq = {}

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ComparisonResult:
    jaccard_similarity: float = 0.0
    shared_top_words: list = None
    unique_a_count: int = 0
    unique_b_count: int = 0
    sentence_length_ratio: float = 0.0
    shared_vocabulary_count: int = 0
    total_vocabulary_union: int = 0

    def __post_init__(self):
        if self.shared_top_words is None:
            self.shared_top_words = []

    def to_dict(self) -> dict:
        return asdict(self)
