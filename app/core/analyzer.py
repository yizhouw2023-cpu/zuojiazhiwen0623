"""Core NLP analysis: analyze_text() and compare_results()."""
from __future__ import annotations
from collections import Counter
from typing import Optional

import jieba.posseg as pseg

from app.core.text_utils import split_sentences, CONTENT_POS_TAGS
from app.models.analysis import AnalysisResult, ComparisonResult


def analyze_text(
    text: str,
    stop_words: Optional[set[str]] = None,
    author_name: str = "",
) -> AnalysisResult:
    """Run full NLP analysis on a text and return an AnalysisResult."""
    if stop_words is None:
        stop_words = set()

    words_with_pos = list(pseg.cut(text))
    all_words = [w.word for w in words_with_pos if w.word.strip()]
    total_words = len(all_words)

    sentences = split_sentences(text)
    total_sentences = len(sentences)
    avg_sentence_length = round(total_words / total_sentences, 2) if total_sentences > 0 else 0.0

    content_words = [
        w.word for w in words_with_pos
        if w.flag in CONTENT_POS_TAGS
        and w.word.strip()
        and w.word not in stop_words
    ]

    word_freq = Counter(content_words)
    top_10 = word_freq.most_common(10)

    return AnalysisResult(
        author_name=author_name,
        total_words=total_words,
        total_sentences=total_sentences,
        avg_sentence_length=avg_sentence_length,
        top_words=[(w, c) for w, c in top_10],
        word_freq=dict(word_freq),
        unique_content_words=len(word_freq),
    )


def compare_results(
    result_a: AnalysisResult,
    result_b: AnalysisResult,
) -> ComparisonResult:
    """Compare two AnalysisResults and return a ComparisonResult."""
    words_a = set(result_a.word_freq.keys())
    words_b = set(result_b.word_freq.keys())

    intersection = words_a & words_b
    union = words_a | words_b
    jaccard = len(intersection) / len(union) if union else 0.0

    top_a = {w for w, _ in result_a.top_words}
    top_b = {w for w, _ in result_b.top_words}
    shared_top = list(top_a & top_b)

    sent_ratio = round(
        result_a.avg_sentence_length / result_b.avg_sentence_length, 2
    ) if result_b.avg_sentence_length > 0 else 0.0

    return ComparisonResult(
        jaccard_similarity=round(jaccard, 4),
        shared_top_words=shared_top,
        unique_a_count=len(words_a - words_b),
        unique_b_count=len(words_b - words_a),
        sentence_length_ratio=sent_ratio,
        shared_vocabulary_count=len(intersection),
        total_vocabulary_union=len(union),
    )
