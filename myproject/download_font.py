"""
download_font.py - Download Sarabun Thai font for PDF
Run: python download_font.py
"""
import urllib.request, os, sys

FONT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'fonts')
os.makedirs(FONT_DIR, exist_ok=True)

FILES = {
    'Sarabun-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/sarabun/Sarabun-Regular.ttf',
    'Sarabun-Bold.ttf':    'https://github.com/google/fonts/raw/main/ofl/sarabun/Sarabun-Bold.ttf',
}

for filename, url in FILES.items():
    dest = os.path.join(FONT_DIR, filename)
    if os.path.exists(dest):
        print(f'  OK (exists): {filename}')
        continue
    print(f'  Downloading {filename}...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, 'wb') as f:
            f.write(r.read())
        print(f'  Saved: {filename} ({os.path.getsize(dest):,} bytes)')
    except Exception as e:
        print(f'  FAILED: {e}')

print('\nFiles in static/fonts/:')
for f in os.listdir(FONT_DIR):
    print(f'  {f}')
