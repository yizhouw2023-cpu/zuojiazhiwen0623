"""File reader for .txt and .docx files."""
from __future__ import annotations
import os

try:
    import docx as _docx
except ImportError:
    _docx = None


def read_file(filepath: str) -> str:
    """Read text from .txt or .docx file. Raises on error."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.txt':
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        if not text.strip():
            raise ValueError("文件内容为空，请选择包含有效文本的文件。")
        return text

    elif ext == '.docx':
        if _docx is None:
            raise ImportError("缺少 python-docx 库")
        doc = _docx.Document(filepath)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        if not paragraphs:
            raise ValueError("Word 文档中未找到有效文本内容。")
        return '\n'.join(paragraphs)

    else:
        raise ValueError(f"不支持的文件格式: {ext}（仅支持 .txt / .docx）")
