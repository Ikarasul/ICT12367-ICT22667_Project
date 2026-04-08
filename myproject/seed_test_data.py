"""
seed_test_data.py — สร้างข้อมูลทดสอบ
- ลูกค้าทดสอบ 1 คน
- ทัวร์ราคา 1 บาท พร้อม Schedule สำหรับสแกน QR

รัน: python seed_test_data.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from django.contrib.auth.hashers import make_password
from tour.db import exec_query

print('\n' + '='*60)
print('  seed_test_data.py')
print('='*60)

# ══════════════════════════════════════════════
# 1. ลูกค้าทดสอบ
# ══════════════════════════════════════════════
print('\n[1/3] Creating test customer...')

TEST_EMAIL    = 'test@toursongkhla.com'
TEST_PASSWORD = 'test1234'
TEST_NAME     = 'ทดสอบ ระบบ'

# ลบเก่าออกก่อน (ถ้ามี)
existing = exec_query("SELECT CustomerID FROM Customers WHERE Email = ?", [TEST_EMAIL])
if existing:
    exec_query("DELETE FROM Customers WHERE Email = ?", [TEST_EMAIL])
    print(f'      ↺ Removed existing test customer')

hashed = make_password(TEST_PASSWORD)
exec_query("""
    INSERT INTO Customers (FullName, Email, Phone, Nationality, PasswordHash)
    VALUES (?, ?, ?, ?, ?)
""", [TEST_NAME, TEST_EMAIL, '0800000001', 'Thai', hashed])

cust = exec_query("SELECT CustomerID FROM Customers WHERE Email = ?", [TEST_EMAIL])
cust_id = cust[0][0]
print(f'      ✓ CustomerID: {cust_id}')
print(f'      Email   : {TEST_EMAIL}')
print(f'      Password: {TEST_PASSWORD}')

# ══════════════════════════════════════════════
# 2. Tour Package ราคา 1 บาท
# ══════════════════════════════════════════════
print('\n[2/3] Creating 1-baht test tour package...')

# ลบเก่าออก
existing_pkg = exec_query(
    "SELECT PackageID FROM TourPackages WHERE PackageName = ?",
    ['[TEST] ทัวร์ทดสอบ QR 1 บาท']
)
if existing_pkg:
    exec_query("DELETE FROM TourPackages WHERE PackageName = ?", ['[TEST] ทัวร์ทดสอบ QR 1 บาท'])

exec_query("""
    INSERT INTO TourPackages (PackageName, Destination, DurationDays, PricePerPerson, Description)
    VALUES (?, ?, ?, ?, ?)
""", [
    '[TEST] ทัวร์ทดสอบ QR 1 บาท',
    'สงขลา (Test)',
    1,
    1,
    'ทัวร์ทดสอบระบบ PromptPay QR — ราคา 1 บาท'
])

pkg = exec_query(
    "SELECT PackageID FROM TourPackages WHERE PackageName = ?",
    ['[TEST] ทัวร์ทดสอบ QR 1 บาท']
)
pkg_id = pkg[0][0]
print(f'      ✓ PackageID: {pkg_id}  |  ราคา: ฿1')

# ══════════════════════════════════════════════
# 3. Schedule (วันออกเดินทาง = พรุ่งนี้)
# ══════════════════════════════════════════════
print('\n[3/3] Creating test schedule...')

# ลบ schedule เก่าของ package นี้
exec_query("DELETE FROM TourSchedules WHERE PackageID = ?", [pkg_id])

exec_query("""
    INSERT INTO TourSchedules (PackageID, DepartureDate, ReturnDate, TotalSeats)
    VALUES (?, DATEADD(day,1,CAST(GETDATE() AS DATE)), DATEADD(day,2,CAST(GETDATE() AS DATE)), 10)
""", [pkg_id])

sched = exec_query(
    "SELECT ScheduleID, DepartureDate FROM TourSchedules WHERE PackageID = ?",
    [pkg_id]
)
sched_id = sched[0][0]
depart   = sched[0][1]
print(f'      ✓ ScheduleID: {sched_id}  |  DepartureDate: {depart}')

# ══════════════════════════════════════════════
# สรุป
# ══════════════════════════════════════════════
print('\n' + '='*60)
print('  ✓ ข้อมูลทดสอบพร้อมแล้ว!')
print('='*60)
print(f'''
  Login ด้วย:
    Email    : {TEST_EMAIL}
    Password : {TEST_PASSWORD}

  จองทัวร์ทดสอบได้ที่:
    http://127.0.0.1:8000/booking/?schedule_id={sched_id}

  หรือไปหน้าหลักแล้วเลือก "[TEST] ทัวร์ทดสอบ QR 1 บาท"
''')
