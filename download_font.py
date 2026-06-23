"""Download Noto Sans SC font for word cloud rendering."""
import urllib.request
import os
import sys

FONT_DIR = os.path.join(os.path.dirname(__file__), "app", "static", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansSC-Regular.ttf")

os.makedirs(FONT_DIR, exist_ok=True)

# Try multiple sources
URLS = [
    "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf",
    "https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf",
]

for url in URLS:
    try:
        print(f"Trying: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            with open(FONT_PATH, "wb") as f:
                f.write(data)
            size_mb = len(data) / (1024 * 1024)
            print(f"SUCCESS: Downloaded {size_mb:.1f} MB to {FONT_PATH}")
            sys.exit(0)
    except Exception as e:
        print(f"Failed: {e}")

print("WARNING: Could not download font. Word cloud may not work.")
print("Please manually download a Chinese .ttf font and place it at:")
print(f"  {FONT_PATH}")
