"""
update_local_images.py
======================
รันหลังจากบันทึกภาพลงใน static/images/tours/ แล้ว
อัพเดต DB ให้ชี้ไปที่ local static files

วิธีรัน: python update_local_images.py
"""
import os
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from tour.db import exec_query

STATIC_BASE = '/static/images/tours'

# ── Map ชื่อ Package → ชื่อไฟล์ที่บันทึกไว้ใน static/images/tours/ ─────────
IMAGE_MAP = {
    'สงขลา เมืองเก่า 1 วัน':      'songkhla_old_town.jpg',
    'หาดใหญ่ ช้อปปิ้ง 1 วัน':     'hatyai_market.jpg',
    'เกาะหนู เกาะแมว 2 วัน':      'koh_lipe.jpg',
    'ทะเลสาบสงขลา 1 วัน':         'thale_noi.jpg',
    'สตูล เกาะตะรุเตา 3 วัน':     'koh_lipe.jpg',          # ใช้ภาพเกาะเดียวกัน
    'ปัตตานี ประวัติศาสตร์ 1 วัน': 'pattani_mosque.jpg',
    'นครศรีธรรมราช 2 วัน':        'nakhon_mahathat.jpg',
    'สงขลา-พัทลุง ธรรมชาติ 2 วัน': 'thale_noi.jpg',         # ทะเลน้อยอยู่พัทลุง
    'หาดสมิหลา ซีฟู้ด 1 วัน':     'samila_mermaid.jpg',
    'ทัวร์ 3 จังหวัด ชายแดน 3 วัน': 'betong_mist.jpg',
}

STATIC_DIR = Path(__file__).resolve().parent / 'static' / 'images' / 'tours'

print('\n' + '='*55)
print('  update_local_images.py')
print('='*55)

packages = exec_query('SELECT PackageID, PackageName FROM TourPackages ORDER BY PackageID')
ok = missing = 0

for row in packages:
    pkg_id, pkg_name = row[0], row[1]
    filename = IMAGE_MAP.get(pkg_name)

    if not filename:
        print(f'  [??] {pkg_name[:40]} — no mapping')
        continue

    filepath = STATIC_DIR / filename
    if not filepath.exists():
        print(f'  [✗] {pkg_name[:40]}')
        print(f'       FILE MISSING: {filepath}')
        print(f'       → บันทึกภาพมาที่ static/images/tours/{filename} ก่อน')
        missing += 1
        continue

    static_url = f'{STATIC_BASE}/{filename}'
    exec_query('UPDATE TourPackages SET ImageURL = ? WHERE PackageID = ?',
               [static_url, pkg_id])
    size = filepath.stat().st_size // 1024
    print(f'  [✓] [{pkg_id:02d}] {pkg_name[:38]}')
    print(f'       → {static_url}  ({size} KB)')
    ok += 1

print(f'\n  ✓ Updated : {ok}')
if missing:
    print(f'  ✗ Missing : {missing}  (ดูรายชื่อไฟล์ด้านบน)')
print('='*55 + '\n')
