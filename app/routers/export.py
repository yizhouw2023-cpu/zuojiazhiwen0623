"""Report export endpoint."""
from __future__ import annotations
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["export"])


class ExportRequest(BaseModel):
    result_a: dict
    result_b: dict
    comparison: dict
    appreciation_text: str = ""


def _format_report(result_a: dict, result_b: dict, comparison: dict, appreciation: str = "") -> str:
    """Generate a formatted TXT report — adapted from desktop app's _format_report()."""
    lines = []
    lines.append("=" * 60)
    lines.append("  作家语言指纹对比分析报告")
    lines.append("=" * 60)
    lines.append(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    def _append_author(title: str, r: dict):
        lines.append("-" * 40)
        lines.append(f"  {title}：{r.get('author_name', '未知')}")
        lines.append("-" * 40)
        lines.append(f"  总词数：{r.get('total_words', 0):,}")
        lines.append(f"  总句数：{r.get('total_sentences', 0):,}")
        lines.append(f"  平均句长：{r.get('avg_sentence_length', 0)} 词/句")
        lines.append(f"  独有内容词数：{r.get('unique_content_words', 0):,}")
        lines.append(f"  前10高频实词：")
        top_words = r.get('top_words', [])
        for i, (word, freq) in enumerate(top_words, 1):
            lines.append(f"    {i:2d}. {word}  —  {freq} 次")
        lines.append("")

    _append_author("作家 A", result_a)
    _append_author("作家 B", result_b)

    if comparison:
        comp = comparison
        lines.append("=" * 60)
        lines.append("  对比分析摘要")
        lines.append("=" * 60)
        lines.append(f"  Jaccard 词汇相似度：{comp.get('jaccard_similarity', 0):.4f}")
        shared = comp.get('shared_top_words', [])
        lines.append(f"  共享高频词：{'、'.join(shared) if shared else '（无）'}")
        lines.append(f"  作家 A 独有词数：{comp.get('unique_a_count', 0):,}")
        lines.append(f"  作家 B 独有词数：{comp.get('unique_b_count', 0):,}")
        lines.append(f"  共用词汇数：{comp.get('shared_vocabulary_count', 0):,}")
        lines.append(f"  词汇并集大小：{comp.get('total_vocabulary_union', 0):,}")
        lines.append(f"  平均句长比 (A/B)：{comp.get('sentence_length_ratio', 0):.2f}")
        lines.append("")

    if appreciation:
        lines.append("=" * 60)
        lines.append("  文章赏析")
        lines.append("=" * 60)
        lines.append("")
        lines.append(appreciation)
        lines.append("")

    lines.append("=" * 60)
    lines.append("  （报告由「作家语言指纹对比分析系统」生成）")
    lines.append("=" * 60)

    return "\n".join(lines)


@router.post("/export/report")
async def export_report(req: ExportRequest):
    """Generate and download a TXT analysis report."""
    try:
        report = _format_report(
            req.result_a, req.result_b, req.comparison, req.appreciation_text
        )
        author_a = req.result_a.get("author_name", "A")
        author_b = req.result_b.get("author_name", "B")
        filename = f"语言指纹对比_{author_a}_vs_{author_b}.txt"

        return Response(
            content=report.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {e}")
