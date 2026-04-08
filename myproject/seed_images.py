"""
seed_images.py — TourSongkhla image seeder
==========================================
ไม่ใช้ Django ORM (ไม่มี Tour model) — ใช้ exec_query (pyodbc) ตรงๆ
เหมาะกับ project นี้ที่เชื่อม SQL Server โดยตรง

วิธีรัน:
    python seed_images.py
หรือ:
    python manage.py shell -c "exec(open('seed_images.py').read())"
"""

import os
import sys

# ── Bootstrap Django ────────────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from tour.db import exec_query

# ════════════════════════════════════════════════════════════════════════
# IMAGE MAP  —  PackageName (exact) → Unsplash image URL
# ════════════════════════════════════════════════════════════════════════
IMAGE_MAP = {
    # 1. เมืองเก่าสงขลา — ถนนนครใน (Wikimedia — ภาพจริง)
    'สงขลา เมืองเก่า 1 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/6/66/Nakhon_Nai_Road%2C_Songkhla.jpg',

    # 2. หาดใหญ่ ช้อปปิ้ง — ตลาดคิมหยง (Wikimedia — ภาพจริง)
    'หาดใหญ่ ช้อปปิ้ง 1 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/2/23/Kim_Yong_Market.jpg',

    # 3. เกาะหนู เกาะแมว — เกาะลิเป (Wikimedia — เกาะใกล้เคียงในภาคใต้)
    'เกาะหนู เกาะแมว 2 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/f/fa/Koh_Lipe_%28island%29%2C_Thailand.jpg',

    # 4. ทะเลสาบสงขลา — ทะเลน้อย พัทลุง (Wikimedia — ทะเลสาบภาคใต้)
    'ทะเลสาบสงขลา 1 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/0/07/Thale_Noi.jpg',

    # 5. สตูล เกาะตะรุเตา — เกาะลิเป สตูล (Wikimedia — ภาพจริง)
    'สตูล เกาะตะรุเตา 3 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/f/fa/Koh_Lipe_%28island%29%2C_Thailand.jpg',

    # 6. ปัตตานี ประวัติศาสตร์ — มัสยิดกลางปัตตานี (Wikimedia — ภาพจริง)
    'ปัตตานี ประวัติศาสตร์ 1 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/8/87/Pattani_Central_Mosque.jpg',

    # 7. นครศรีธรรมราช — วัดพระมหาธาตุ (Wikimedia — ภาพจริง)
    'นครศรีธรรมราช 2 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/3/36/Wat_Phra_Mahathat_Woramahawihan_%28I%29.jpg',

    # 8. สงขลา-พัทลุง ธรรมชาติ — ทะเลน้อย (Wikimedia — ธรรมชาติภาคใต้จริงๆ)
    'สงขลา-พัทลุง ธรรมชาติ 2 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/0/07/Thale_Noi.jpg',

    # 9. หาดสมิหลา — นางเงือกทอง (Wikimedia — icon ของสงขลา)
    'หาดสมิหลา ซีฟู้ด 1 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/4/4b/Golden_Mermaid_Statue%2C_Samila_Beach.jpg',

    # 10. ทัวร์ 3 จังหวัด — ทะเลหมอก เบตง (Wikimedia — ภาพใต้สุดแดนสยาม)
    'ทัวร์ 3 จังหวัด ชายแดน 3 วัน':
        'https://upload.wikimedia.org/wikipedia/commons/a/af/The_Sea_of_Mist_Ai_Yerweng%2C_Betong.jpg',
}

# Fallback — ภาพทั่วไปถ้าไม่มีใน map
FALLBACK_URL = (
    'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4'
    '?w=800&q=85&fit=crop'
)

# ════════════════════════════════════════════════════════════════════════
# STEP 1 — Add ImageURL column (safe: checks existence first)
# ════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('  TourSongkhla — Image Seeder')
print('='*60)

print('\n[1/3] Adding ImageURL column to TourPackages...')
try:
    exec_query("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME  = 'TourPackages'
              AND COLUMN_NAME = 'ImageURL'
        )
        ALTER TABLE TourPackages
            ADD ImageURL NVARCHAR(500) NULL
    """)
    print('      ✓ Column ready')
except Exception as e:
    print(f'      ✗ Error: {e}')
    sys.exit(1)

# ════════════════════════════════════════════════════════════════════════
# STEP 2 — Update each TourPackage row
# ════════════════════════════════════════════════════════════════════════
print('\n[2/3] Updating image URLs...')

packages = exec_query(
    'SELECT PackageID, PackageName FROM TourPackages ORDER BY PackageID'
)
if not packages:
    print('      ✗ No TourPackages found — run setup_db.py first')
    sys.exit(1)

ok = 0
for row in packages:
    pkg_id   = row[0]
    pkg_name = row[1]
    url      = IMAGE_MAP.get(pkg_name, FALLBACK_URL)
    source   = 'MAP' if pkg_name in IMAGE_MAP else 'FALLBACK'
    try:
        exec_query(
            'UPDATE TourPackages SET ImageURL = ? WHERE PackageID = ?',
            [url, pkg_id]
        )
        print(f'      ✓ [{pkg_id:02d}] ({source}) {pkg_name}')
        ok += 1
    except Exception as e:
        print(f'      ✗ [{pkg_id:02d}] {pkg_name} — {e}')

print(f'\n      Updated {ok}/{len(packages)} packages')

# ════════════════════════════════════════════════════════════════════════
# STEP 3 — Recreate vw_ScheduleAvailability with ImageURL
# ════════════════════════════════════════════════════════════════════════
print('\n[3/3] Rebuilding vw_ScheduleAvailability with ImageURL...')
try:
    exec_query("IF OBJECT_ID('vw_ScheduleAvailability','V') IS NOT NULL DROP VIEW vw_ScheduleAvailability")
    exec_query("""
        CREATE VIEW vw_ScheduleAvailability AS
        SELECT
            s.ScheduleID,
            ISNULL(tp.TourName_en,  tp.PackageName)    AS TourName,
            ISNULL(tp.Destination_en, tp.Destination)  AS Destination,
            s.DepartureDate,
            s.ReturnDate,
            s.TotalSeats                               AS Capacity,
            s.TotalSeats - ISNULL((
                SELECT SUM(b.NumAdults + ISNULL(b.NumChildren,0))
                FROM   Bookings b
                WHERE  b.ScheduleID = s.ScheduleID
                  AND  b.Status    != 'Cancelled'
            ), 0)                                      AS AvailableSeats,
            tp.PricePerPerson                          AS Price,
            tp.PackageID                               AS TourID,
            ISNULL(g.FullName, N'TBA')                 AS GuideName,
            ISNULL(tp.TourName_en,  tp.PackageName)    AS TourName_en,
            ISNULL(tp.Destination_en, tp.Destination)  AS Destination_en,
            ISNULL(tp.ImageURL, N'')                   AS ImageURL
        FROM  TourSchedules s
        JOIN  TourPackages  tp ON s.PackageID  = tp.PackageID
        LEFT JOIN Guides    g  ON s.GuideID    = g.GuideID
    """)
    print('      ✓ View recreated (ImageURL is now column index 12)')
except Exception as e:
    print(f'      ✗ View error: {e}')

# ════════════════════════════════════════════════════════════════════════
# VERIFY
# ════════════════════════════════════════════════════════════════════════
print('\n' + '-'*60)
print('Verification — first 3 schedules:')
try:
    rows = exec_query("SELECT TOP 3 ScheduleID, TourName, ImageURL FROM vw_ScheduleAvailability")
    for r in rows:
        img_ok = '✓' if r[2] else '✗ (empty)'
        print(f'  Schedule {r[0]} | {r[1][:30]:<30} | Image {img_ok}')
except Exception as e:
    print(f'  Error: {e}')

print('\n' + '='*60)
print('  Done! Now update tours.html to display tour.data.12')
print('='*60 + '\n')
