"""Word cloud generation — adapted from desktop app for web server use."""
from __future__ import annotations
import os
from io import BytesIO
from typing import Optional

import matplotlib
matplotlib.use('Agg')
from wordcloud import WordCloud
from PIL import Image

# Font path: wordcloud_gen.py is in app/core/, so two dirname levels to reach app/
_FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "fonts")
WC_FONT_PATH = os.path.join(_FONTS_DIR, "NotoSansSC-Regular.ttf")

# Fallback: try system font paths
if not os.path.exists(WC_FONT_PATH):
    _CANDIDATES = [
        "C:/Windows/Fonts/msyh.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for _p in _CANDIDATES:
        if os.path.exists(_p):
            WC_FONT_PATH = _p
            break

# Color scheme (mirrors desktop app)
COLORS = {
    "primary": "#2E86AB",
    "wordcloud_bg": "#FFFFFF",
}


def generate_wordcloud(
    word_freq: dict[str, int],
    author_name: str = "",
    width: int = 600,
    height: int = 400,
    font_path: Optional[str] = None,
) -> Optional[Image.Image]:
    """Generate a word cloud PIL Image from word frequency dict."""
    if not word_freq:
        return None

    fp = font_path or WC_FONT_PATH

    try:
        wc = WordCloud(
            font_path=fp,
            width=width,
            height=height,
            background_color=COLORS["wordcloud_bg"],
            max_words=150,
            max_font_size=80,
            min_font_size=10,
            prefer_horizontal=0.9,
            colormap="viridis",
            contour_width=1,
            contour_color=COLORS["primary"],
        )
        wc.generate_from_frequencies(word_freq)
        return wc.to_image()
    except Exception as e:
        print(f"词云生成失败: {e}")
        return None


def wordcloud_to_bytes(
    image: Image.Image,
    format: str = "PNG",
) -> bytes:
    """Convert a PIL Image to bytes."""
    buf = BytesIO()
    if format.upper() == "JPEG" or format.upper() == "JPG":
        image.convert("RGB").save(buf, "JPEG", quality=95)
    else:
        image.save(buf, "PNG")
    buf.seek(0)
    return buf.getvalue()
