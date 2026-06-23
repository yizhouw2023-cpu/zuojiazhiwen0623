"""Report export endpoints — TXT and PDF."""
from __future__ import annotations
import os
import io
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


# ---- Font path for PDF ----
_APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FONT_PATH = os.path.join(_APP_DIR, "static", "fonts", "NotoSansSC-Regular.ttf")
if not os.path.exists(_FONT_PATH):
    _FONT_PATH = "C:/Windows/Fonts/msyh.ttc"  # Windows fallback


# ================================================================
#  TXT Export
# ================================================================

def _format_txt(result_a: dict, result_b: dict, comparison: dict, appreciation: str = "") -> str:
    """Generate a formatted TXT report."""
    sep = "=" * 60
    sub = "-" * 40
    lines = [sep, "  作家语言指纹对比分析报告", sep,
             f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]

    for title, r in [("作家 A", result_a), ("作家 B", result_b)]:
        lines.append(sub)
        lines.append(f"  {title}：{r.get('author_name', '未知')}")
        lines.append(sub)
        lines.append(f"  总词数：{r.get('total_words', 0):,}")
        lines.append(f"  总句数：{r.get('total_sentences', 0):,}")
        lines.append(f"  平均句长：{r.get('avg_sentence_length', 0)} 词/句")
        lines.append(f"  独有内容词数：{r.get('unique_content_words', 0):,}")
        lines.append(f"  前10高频实词：")
        for i, (w, f) in enumerate(r.get('top_words', []), 1):
            lines.append(f"    {i:2d}. {w}  —  {f} 次")
        lines.append("")

    if comparison:
        c = comparison
        lines.append(sep); lines.append("  对比分析摘要"); lines.append(sep)
        lines.append(f"  Jaccard 词汇相似度：{c.get('jaccard_similarity', 0):.4f}")
        shared = c.get('shared_top_words', [])
        lines.append(f"  共享高频词：{'、'.join(shared) if shared else '（无）'}")
        lines.append(f"  作家 A 独有词数：{c.get('unique_a_count', 0):,}")
        lines.append(f"  作家 B 独有词数：{c.get('unique_b_count', 0):,}")
        lines.append(f"  共用词汇数：{c.get('shared_vocabulary_count', 0):,}")
        lines.append(f"  词汇并集大小：{c.get('total_vocabulary_union', 0):,}")
        lines.append(f"  平均句长比 (A/B)：{c.get('sentence_length_ratio', 0):.2f}")
        lines.append("")

    if appreciation:
        lines.append(sep); lines.append("  文章赏析"); lines.append(sep)
        lines.append(""); lines.append(appreciation); lines.append("")

    lines.append(sep)
    lines.append("  （报告由「作家语言指纹对比分析系统」生成）")
    lines.append(sep)
    return "\n".join(lines)


@router.post("/export/report")
async def export_txt(req: ExportRequest):
    """Download TXT report."""
    try:
        report = _format_txt(req.result_a, req.result_b, req.comparison, req.appreciation_text)
        safe_name = f"{req.result_a.get('author_name', 'A')}_vs_{req.result_b.get('author_name', 'B')}"
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in '._- ')
        filename = f"语言指纹对比_{safe_name}.txt"

        encoded_filename = filename.encode("utf-8").decode("latin-1", errors="replace")
        return Response(
            content=report.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {e}")


# ================================================================
#  PDF Export (beautiful layout)
# ================================================================

def _build_pdf(result_a: dict, result_b: dict, comparison: dict, appreciation: str = "") -> bytes:
    """Generate a beautifully formatted PDF report using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Register Chinese font
    if os.path.exists(_FONT_PATH):
        pdf.add_font("CJK", "", _FONT_PATH, uni=True)
        font_name = "CJK"
    else:
        font_name = "Helvetica"

    # === Header ===
    pdf.set_fill_color(46, 134, 171)  # primary color
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(font_name, "", 18)
    pdf.set_y(8)
    pdf.cell(0, 10, "作家语言指纹对比分析报告", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_name, "", 9)
    pdf.cell(0, 8, f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # === Author A ===
    _pdf_author_section(pdf, font_name, "作家 A", result_a)
    pdf.ln(4)

    # === Author B ===
    _pdf_author_section(pdf, font_name, "作家 B", result_b)
    pdf.ln(4)

    # === Comparison ===
    if comparison:
        c = comparison
        pdf.set_fill_color(240, 244, 255)
        pdf.set_text_color(162, 59, 114)
        pdf.set_font(font_name, "", 14)
        pdf.cell(0, 10, "对比分析摘要", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(162, 59, 114)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
        pdf.ln(4)

        pdf.set_text_color(44, 62, 80)
        pdf.set_font(font_name, "", 10)
        j = c.get('jaccard_similarity', 0)
        label = "高度相似" if j > 0.5 else ("中等相似" if j > 0.25 else "差异较大") if j > 0 else "—"
        items = [
            ("Jaccard 词汇相似度", f"{j:.4f}  ({label})"),
            ("共享高频词", "、".join(c.get('shared_top_words', [])) if c.get('shared_top_words') else "（无）"),
            ("作家 A 独有词汇数", f"{c.get('unique_a_count', 0):,}"),
            ("作家 B 独有词汇数", f"{c.get('unique_b_count', 0):,}"),
            ("共用词汇总数", f"{c.get('shared_vocabulary_count', 0):,}"),
            ("词汇并集大小", f"{c.get('total_vocabulary_union', 0):,}"),
            ("平均句长比 (A/B)", f"{c.get('sentence_length_ratio', 0):.2f}"),
        ]
        for label, val in items:
            pdf.set_font(font_name, "", 10)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(55, 8, label + "：")
            pdf.set_text_color(46, 134, 171)
            pdf.cell(0, 8, val, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # === Appreciation ===
    if appreciation.strip():
        pdf.set_text_color(241, 143, 1)
        pdf.set_font(font_name, "", 14)
        pdf.cell(0, 10, "文章赏析", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(241, 143, 1)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
        pdf.ln(4)
        pdf.set_text_color(44, 62, 80)
        pdf.set_font(font_name, "", 10)

        # Clean markdown markers for PDF
        clean = appreciation
        for ch in ['#', '*', '`']:
            clean = clean.replace(ch, '')
        pdf.multi_cell(0, 6, clean)

    # === Footer ===
    pdf.ln(8)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
    pdf.ln(4)
    pdf.set_text_color(132, 146, 166)
    pdf.set_font(font_name, "", 8)
    pdf.cell(0, 6, "本报告由「作家语言指纹对比分析系统」自动生成", align="C")

    return pdf.output()


def _pdf_author_section(pdf: FPDF, font_name: str, title: str, r: dict):
    """Render one author's analysis section in PDF."""
    name = r.get('author_name', '未知')
    pdf.set_fill_color(46, 134, 171)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(font_name, "", 12)
    pdf.cell(0, 9, f"  {title}：{name}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_text_color(44, 62, 80)
    pdf.set_font(font_name, "", 10)
    stats = [
        ("总词数", f"{r.get('total_words', 0):,}"),
        ("总句数", f"{r.get('total_sentences', 0):,}"),
        ("平均句长", f"{r.get('avg_sentence_length', 0)} 词/句"),
        ("独有内容词数", f"{r.get('unique_content_words', 0):,}"),
    ]
    for label, val in stats:
        pdf.cell(50, 7, f"  {label}：{val}")

    pdf.ln(10)
    pdf.set_text_color(46, 134, 171)
    pdf.set_font(font_name, "", 10)
    pdf.cell(0, 7, "  前10高频实词：", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(44, 62, 80)

    top_words = r.get('top_words', [])
    if top_words:
        for i, (w, f) in enumerate(top_words):
            col = i % 5
            if col == 0:
                pdf.cell(10, 7, "", new_x="RIGHT")  # indent
            pdf.cell(30, 7, f"{i+1}. {w}({f})")
            if col == 4 or i == len(top_words) - 1:
                pdf.ln(7)
    else:
        pdf.cell(0, 7, "  （无内容词）", new_x="LMARGIN", new_y="NEXT")


@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    """Download beautiful PDF report."""
    try:
        pdf_bytes = _build_pdf(req.result_a, req.result_b, req.comparison, req.appreciation_text)
        safe_name = f"{req.result_a.get('author_name', 'A')}_vs_{req.result_b.get('author_name', 'B')}"
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in '._- ')
        filename = f"语言指纹对比_{safe_name}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="缺少 fpdf2 库，无法生成 PDF")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {e}")
