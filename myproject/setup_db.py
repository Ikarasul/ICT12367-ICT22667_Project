"""
setup_db.py  ·  TourSongkhla Database Rebuild Script
=====================================================
รัน:  python setup_db.py

ใช้ sqlcmd (native) ผ่าน subprocess เพื่อรองรับ GO statements
จะ DROP และ CREATE ตารางทั้งหมดใหม่ พร้อม sample data + views + SPs
"""

import pyodbc
import subprocess
import sys
import os

# ─── CONFIG ────────────────────────────────────────────────────────────────────
SERVER   = r'DESKTOP-S27JDCN\RAVEN'
DATABASE = 'TourSongkhla'
DRIVER   = 'ODBC Driver 17 for SQL Server'

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
SQL_FILES = [
    os.path.join(BASE_DIR, 'sql', 'schema.sql'),
    os.path.join(BASE_DIR, 'sql', 'setup_procedures.sql'),
    os.path.join(BASE_DIR, 'sql', 'add_bilingual_columns.sql'),
]
# ───────────────────────────────────────────────────────────────────────────────


def get_connection(database='master'):
    conn_str = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str, autocommit=True)


def ensure_database_exists():
    """สร้าง TourSongkhla ถ้ายังไม่มี"""
    conn   = get_connection(database='master')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases WHERE name = ?", [DATABASE])
    if not cursor.fetchone():
        print(f"  Creating database '{DATABASE}'...")
        cursor.execute(f"CREATE DATABASE [{DATABASE}]")
        print(f"  ✓ Database '{DATABASE}' created.")
    else:
        print(f"  ✓ Database '{DATABASE}' already exists — OK")
    cursor.close()
    conn.close()


def run_sqlcmd(filepath):
    """
    รัน SQL file ผ่าน sqlcmd (native tool) — รองรับ GO statements 100%
    ใช้ Windows Authentication (-E)
    """
    filename = os.path.basename(filepath)
    print(f"\n  Running via sqlcmd: {filename}")

    cmd = [
        'sqlcmd',
        '-S', SERVER,
        '-d', DATABASE,
        '-E',                   # Windows Authentication
        '-i', filepath,
        '-f', '65001',          # UTF-8
        '-C',                   # Trust Server Certificate (Driver 18+)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )

        # แสดง output (PRINT statements จาก SQL)
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    print(f"    {line}")

        if result.returncode != 0:
            print(f"    [!] sqlcmd error (returncode={result.returncode}):")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines()[:10]:
                    print(f"        {line}")
            return False

        print(f"    ✓ {filename} — completed successfully")
        return True

    except FileNotFoundError:
        print("    [FATAL] 'sqlcmd' not found in PATH.")
        print("    ติดตั้ง: SQL Server Command Line Utilities")
        print("    ดาวน์โหลด: https://aka.ms/sqlcmdtools")
        return False
    except Exception as e:
        print(f"    [!] Unexpected error: {e}")
        return False


def verify_connection():
    """ทดสอบ connection + ตรวจนับตาราง/ข้อมูล"""
    print("\n─── Verifying Database ───────────────────────────────────────")
    conn   = get_connection(database=DATABASE)
    cursor = conn.cursor()

    checks = [
        ("Tables",    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"),
        ("Views",     "SELECT COUNT(*) FROM INFORMATION_SCHEMA.VIEWS"),
        ("SPs",       "SELECT COUNT(*) FROM sys.procedures"),
        ("Packages",  "SELECT COUNT(*) FROM TourPackages"),
        ("Schedules", "SELECT COUNT(*) FROM TourSchedules"),
        ("Guides",    "SELECT COUNT(*) FROM Guides"),
        ("Employees", "SELECT COUNT(*) FROM Employees"),
    ]

    all_ok = True
    for label, sql in checks:
        try:
            cursor.execute(sql)
            count = cursor.fetchone()[0]
            status = "✓" if count > 0 else "⚠  (empty)"
            print(f"  {label:12s} : {count:3d}  {status}")
        except Exception as e:
            print(f"  {label:12s} : ERROR — {e}")
            all_ok = False

    # แสดงรายชื่อตารางทั้งหมด
    try:
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n  Tables ({len(tables)}): {', '.join(tables)}")
    except Exception:
        pass

    cursor.close()
    conn.close()
    return all_ok


def main():
    print("=" * 62)
    print("  TourSongkhla — Database Rebuild")
    print(f"  Server  : {SERVER}")
    print(f"  Database: {DATABASE}")
    print("=" * 62)

    # Step 1: Ensure DB exists
    print("\n─── Step 1: Ensure Database Exists ──────────────────────────")
    try:
        ensure_database_exists()
    except Exception as e:
        print(f"  [FATAL] Cannot connect to SQL Server: {e}")
        print("\n  Checklist:")
        print(f"  1. SQL Server '{SERVER}' ทำงานอยู่หรือไม่?")
        print("  2. ODBC Driver 17 for SQL Server ติดตั้งแล้วหรือยัง?")
        print("     ดาวน์โหลด: https://aka.ms/downloadmsodbcsql")
        sys.exit(1)

    # Step 2: Execute SQL files via sqlcmd
    print("\n─── Step 2: Execute SQL Files (sqlcmd) ──────────────────────")
    all_success = True
    for sql_file in SQL_FILES:
        if not os.path.exists(sql_file):
            print(f"  [SKIP] File not found: {sql_file}")
            continue
        ok = run_sqlcmd(sql_file)
        if not ok:
            all_success = False

    if not all_success:
        print("\n  [WARNING] Some SQL files had errors — check output above")

    # Step 3: Verify
    ok = verify_connection()

    # Step 4: Summary
    print("\n─── Summary ──────────────────────────────────────────────────")
    if ok:
        print("  ✅  TourSongkhla — Database rebuild complete!")
        print("\n  Django App Credentials:")
        print("  Employee (Admin) : admin@toursongkhla.com / admin1234")
        print("  Employee (Sales) : sales@toursongkhla.com / sales1234")
        print("  (Customers: ลงทะเบียนผ่าน /register/)")
        print("\n  Start server:")
        print("  cd Pro\\myproject && python manage.py runserver")
    else:
        print("  ❌  Some checks failed — see errors above")
    print("=" * 62)


if __name__ == '__main__':
    main()
