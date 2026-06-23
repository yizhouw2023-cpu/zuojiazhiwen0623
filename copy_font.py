"""Copy system Chinese font or download for word cloud.
Usage: python copy_font.py
Run from the project root directory (writer-fingerprint-web/).
"""
import shutil
import os
import sys

# Resolve project root from script location
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(PROJECT_ROOT, "app", "static", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansSC-Regular.ttf")
os.makedirs(FONT_DIR, exist_ok=True)

# Strategy 1: Copy from Windows system fonts
SYSTEM_FONTS = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]
for src in SYSTEM_FONTS:
    if os.path.exists(src):
        try:
            shutil.copy2(src, FONT_PATH)
            size_mb = os.path.getsize(FONT_PATH) / (1024 * 1024)
            print(f"OK: Copied {src} -> {FONT_PATH} ({size_mb:.1f} MB)")
            sys.exit(0)
        except Exception as e:
            print(f"Copy failed: {e}")

# Strategy 2: Download
import urllib.request

URLS = [
    "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf",
]
for url in URLS:
    try:
        print(f"Downloading: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(FONT_PATH, "wb") as f:
                f.write(resp.read())
        size_mb = os.path.getsize(FONT_PATH) / (1024 * 1024)
        print(f"OK: Downloaded ({size_mb:.1f} MB)")
        sys.exit(0)
    except Exception as e:
        print(f"Download failed: {e}")

print("FAILED: No font available. Please manually copy a Chinese .ttf font to:")
print(f"  {FONT_PATH}")
print("On Windows, you can copy from: C:\\Windows\\Fonts\\msyh.ttc")
