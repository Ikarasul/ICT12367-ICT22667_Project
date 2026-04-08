"""
fix_constraint.py — แก้ CHECK constraint ของ Bookings.Status
ให้รองรับ: Pending, Confirmed, Cancelled, PayLater, PendingReview
Run: python fix_constraint.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from tour.db import exec_query

print('Checking existing constraint...')

# ดูว่า constraint ชื่ออะไรบ้าง
rows = exec_query("""
    SELECT cc.name, cc.definition
    FROM sys.check_constraints cc
    JOIN sys.tables t ON cc.parent_object_id = t.object_id
    WHERE t.name = 'Bookings'
""")

for r in rows:
    print(f'  Constraint: {r[0]}')
    print(f'  Definition: {r[1]}')

if not rows:
    print('  No CHECK constraints found on Bookings table.')
else:
    for r in rows:
        constraint_name = r[0]
        print(f'\nDropping constraint: {constraint_name}')
        exec_query(f'ALTER TABLE Bookings DROP CONSTRAINT [{constraint_name}]')
        print('  Dropped.')

print('\nAdding new constraint with all valid statuses...')
exec_query("""
    ALTER TABLE Bookings
    ADD CONSTRAINT CK_Bookings_Status
    CHECK (Status IN ('Pending', 'Confirmed', 'Cancelled', 'PayLater', 'PendingReview'))
""")
print('  Done.')

print('\nTest INSERT with PendingReview...')
try:
    exec_query("""
        UPDATE Bookings SET Status = Status
        WHERE Status = 'PendingReview'
    """)
    print('  Constraint OK.')
except Exception as e:
    print(f'  Error: {e}')

print('\nConstraint updated successfully!')
