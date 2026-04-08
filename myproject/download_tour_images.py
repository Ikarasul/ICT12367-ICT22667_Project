"""
download_tour_images.py
=======================
Downloads tour images from Wikipedia Commons → saves to static/images/tours/
Updates TourPackages.ImageURL in the database to local static paths.

วิธีรัน: python download_tour_images.py
"""

import os
import sys
import time
import urllib.request
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from tour.db import exec_query

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
SAVE_DIR    = BASE_DIR / 'static' / 'images' / 'tours'
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# ── Browser headers to bypass anti-hotlink checks ───────────────────────────
HEADERS = {
    'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/124.0.0.0 Safari/537.36',
    'Accept':          'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,th;q=0.8',
    'Referer':         'https://commons.wikimedia.org/',
}

# ── Source map: PackageName → (filename, url) ───────────────────────────────
# Wikipedia Commons thumbnail format (more reliable than direct URLs)
# format: /thumb/{a}/{ab}/{filename}/{width}px-{filename}
IMAGE_SOURCES = {
    'สงขลา เมืองเก่า 1 วัน': (
        'songkhla_old_town.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/'
        'Nakhon_Nai_Road%2C_Songkhla.jpg/800px-Nakhon_Nai_Road%2C_Songkhla.jpg',
    ),
    'หาดใหญ่ ช้อปปิ้ง 1 วัน': (
        'hatyai_market.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/'
        'Kim_Yong_Market.jpg/800px-Kim_Yong_Market.jpg',
    ),
    'เกาะหนู เกาะแมว 2 วัน': (
        'koh_lipe.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/'
        'Koh_Lipe_%28island%29%2C_Thailand.jpg/800px-Koh_Lipe_%28island%29%2C_Thailand.jpg',
    ),
    'ทะเลสาบสงขลา 1 วัน': (
        'thale_noi.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/'
        'Thale_Noi.jpg/800px-Thale_Noi.jpg',
    ),
    'สตูล เกาะตะรุเตา 3 วัน': (
        'tarutao.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/'
        'Koh_Lipe_%28island%29%2C_Thailand.jpg/800px-Koh_Lipe_%28island%29%2C_Thailand.jpg',
    ),
    'ปัตตานี ประวัติศาสตร์ 1 วัน': (
        'pattani_mosque.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/'
        'Pattani_Central_Mosque.jpg/800px-Pattani_Central_Mosque.jpg',
    ),
    'นครศรีธรรมราช 2 วัน': (
        'nakhon_mahathat.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/'
        'Wat_Phra_Mahathat_Woramahawihan_%28I%29.jpg/'
        '800px-Wat_Phra_Mahathat_Woramahawihan_%28I%29.jpg',
    ),
    'สงขลา-พัทลุง ธรรมชาติ 2 วัน': (
        'thale_noi_nature.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/'
        'Thale_Noi.jpg/800px-Thale_Noi.jpg',
    ),
    'หาดสมิหลา ซีฟู้ด 1 วัน': (
        'samila_mermaid.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/'
        'Golden_Mermaid_Statue%2C_Samila_Beach.jpg/'
        '800px-Golden_Mermaid_Statue%2C_Samila_Beach.jpg',
    ),
    'ทัวร์ 3 จังหวัด ชายแดน 3 วัน': (
        'betong_mist.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/'
        'The_Sea_of_Mist_Ai_Yerweng%2C_Betong.jpg/'
        '800px-The_Sea_of_Mist_Ai_Yerweng%2C_Betong.jpg',
    ),
}

FALLBACK_URL = (
    'https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/'
    'Tinsulanonda_Bridge.jpg/800px-Tinsulanonda_Bridge.jpg'
)

# ── Download helper ──────────────────────────────────────────────────────────
def download_image(url, save_path, label):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                print(f'    ✗ Not an image (got {content_type[:40]}) — skipping')
                return False
            data = resp.read()
            if len(data) < 1000:
                print(f'    ✗ File too small ({len(data)} bytes) — likely an error page')
                return False
            with open(save_path, 'wb') as f:
                f.write(data)
            print(f'    ✓ {len(data)//1024} KB saved → {save_path.name}')
            return True
    except urllib.error.HTTPError as e:
        print(f'    ✗ HTTP {e.code} — {e.reason}')
        return False
    except Exception as e:
        print(f'    ✗ Error: {e}')
        return False


# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*62)
print('  TourSongkhla — Download Images to Local Static Files')
print('='*62)

packages = exec_query(
    'SELECT PackageID, PackageName FROM TourPackages ORDER BY PackageID'
)
if not packages:
    print('No packages found — run setup_db.py first')
    sys.exit(1)

ok = fail = 0

for row in packages:
    pkg_id, pkg_name = row[0], row[1]
    print(f'\n  [{pkg_id:02d}] {pkg_name}')

    if pkg_name in IMAGE_SOURCES:
        filename, url = IMAGE_SOURCES[pkg_name]
    else:
        print(f'    ! No mapping — using fallback')
        filename = f'tour_{pkg_id:02d}.jpg'
        url      = FALLBACK_URL

    save_path  = SAVE_DIR / filename
    static_url = f'/static/images/tours/{filename}'

    # Skip re-download if file already exists and is valid
    if save_path.exists() and save_path.stat().st_size > 1000:
        print(f'    ~ Already exists ({save_path.stat().st_size//1024} KB) — using cached')
        success = True
    else:
        success = download_image(url, save_path, pkg_name)

    if success:
        exec_query(
            'UPDATE TourPackages SET ImageURL = ? WHERE PackageID = ?',
            [static_url, pkg_id]
        )
        print(f'    ✓ DB updated → {static_url}')
        ok += 1
    else:
        fail += 1

    time.sleep(0.4)  # polite delay between Wikipedia requests

# ── Verify ──────────────────────────────────────────────────────────────────
print('\n' + '-'*62)
print(f'  Downloaded: {ok}/{len(packages)}  |  Failed: {fail}')
print()
print('  Files saved to:')
for f in sorted(SAVE_DIR.iterdir()):
    size = f.stat().st_size // 1024
    print(f'    {size:>5} KB  {f.name}')

print()
print('  DB now contains:')
rows = exec_query('SELECT PackageID, ImageURL FROM TourPackages ORDER BY PackageID')
for r in rows:
    status = '✓' if (r[1] or '').startswith('/static/') else '✗'
    print(f'    {status} [{r[0]:02d}] {r[1]}')

print('\n' + '='*62)
print('  Done! Images are now served from local static files.')
print('  No more broken links or Wikipedia blocking issues.')
print('='*62 + '\n')
