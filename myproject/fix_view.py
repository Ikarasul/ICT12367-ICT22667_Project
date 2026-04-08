"""
fix_view.py — สร้าง vw_ScheduleAvailability ใหม่ให้ถูกต้อง
รัน: python fix_view.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from tour.db import exec_query

print('\n' + '='*60)
print('  fix_view.py — Recreating vw_ScheduleAvailability')
print('='*60)

# ── Step 1: ตรวจสอบ columns ที่มีจริงใน TourPackages ────────────
print('\n[1/3] Checking TourPackages columns...')
cols = exec_query("""
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'TourPackages' ORDER BY ORDINAL_POSITION
""")
col_names = [r[0] for r in cols]
print(f'      Columns: {col_names}')

has_image_url    = 'ImageURL'    in col_names
has_tourname_en  = 'TourName_en' in col_names
has_dest_en      = 'Destination_en' in col_names

# ── Step 2: เพิ่ม ImageURL ถ้ายังไม่มี ──────────────────────────
if not has_image_url:
    print('\n[2/3] Adding ImageURL column...')
    exec_query("""
        ALTER TABLE TourPackages ADD ImageURL NVARCHAR(500) NULL
    """)
    print('      ✓ Added ImageURL')
else:
    print('\n[2/3] ImageURL column already exists ✓')

# ── Step 3: สร้าง View ใหม่ใช้เฉพาะ columns ที่มีจริง ──────────
print('\n[3/3] Recreating vw_ScheduleAvailability...')

tour_name_expr = (
    "ISNULL(tp.TourName_en, tp.PackageName)" if has_tourname_en
    else "tp.PackageName"
)
dest_expr = (
    "ISNULL(tp.Destination_en, tp.Destination)" if has_dest_en
    else "tp.Destination"
)

try:
    exec_query("IF OBJECT_ID('vw_ScheduleAvailability','V') IS NOT NULL DROP VIEW vw_ScheduleAvailability")
    exec_query(f"""
        CREATE VIEW vw_ScheduleAvailability AS
        SELECT
            s.ScheduleID,
            {tour_name_expr}                               AS TourName,
            {dest_expr}                                    AS Destination,
            s.DepartureDate,
            s.ReturnDate,
            s.TotalSeats                                   AS Capacity,
            s.TotalSeats - ISNULL((
                SELECT SUM(b.NumAdults + ISNULL(b.NumChildren,0))
                FROM   Bookings b
                WHERE  b.ScheduleID = s.ScheduleID
                  AND  b.Status    != 'Cancelled'
            ), 0)                                          AS AvailableSeats,
            tp.PricePerPerson                              AS Price,
            tp.PackageID                                   AS TourID,
            ISNULL(g.FullName, N'TBA')                     AS GuideName,
            {tour_name_expr}                               AS TourName_en,
            {dest_expr}                                    AS Destination_en,
            ISNULL(tp.ImageURL, N'')                       AS ImageURL
        FROM  TourSchedules s
        JOIN  TourPackages  tp ON s.PackageID = tp.PackageID
        LEFT JOIN Guides    g  ON s.GuideID   = g.GuideID
    """)
    print('      ✓ View recreated successfully')
except Exception as e:
    print(f'      ✗ ERROR: {e}')
    raise

# ── Verify ──────────────────────────────────────────────────────
print('\n' + '-'*60)
print('Verification — first 3 rows:')
rows = exec_query("SELECT TOP 3 ScheduleID, TourName, Destination, AvailableSeats, ImageURL FROM vw_ScheduleAvailability")
if rows:
    for r in rows:
        img = '✓ has image' if r[4] else '✗ no image'
        print(f'  [{r[0]}] {str(r[1])[:30]:<30} | {str(r[2])[:15]:<15} | seats:{r[3]} | {img}')
else:
    print('  ⚠ No rows returned — check TourSchedules table has data')

print('\n' + '='*60)
print('  Done! Restart the Django server and reload the page.')
print('='*60 + '\n')
