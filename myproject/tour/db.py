# tour/db.py
# ═══════════════════════════════════════
# Helper สำหรับเชื่อม SQL Server ผ่าน pyodbc
# ═══════════════════════════════════════
import pyodbc
from django.conf import settings

class DatabaseError(Exception):
    """Custom exception for general database errors"""
    pass

class ObjectNotFoundError(DatabaseError):
    """Custom exception when a Stored Procedure or View is missing"""
    pass

def get_connection():
    """สร้าง connection กับ SQL Server"""
    cfg = settings.MSSQL_CONFIG
    conn_str = (
        f"DRIVER={{{cfg['DRIVER']}}};"
        f"SERVER={cfg['SERVER']};"
        f"DATABASE={cfg['DATABASE']};"
    )
    if cfg.get('TRUSTED_CONNECTION') == 'yes':
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={cfg['UID']};PWD={cfg['PWD']};"
    return pyodbc.connect(conn_str)

def check_sp_exists(cursor, sp_name):
    """ตรวจสอบว่ามี Stored Procedure นี้ใน DB หรือไม่"""
    cursor.execute("SELECT object_id FROM sys.procedures WHERE name = ?", [sp_name])
    return cursor.fetchone() is not None

def exec_sp(sp_name, params=None):
    """
    เรียก Stored Procedure และ return ผลลัพธ์เป็น list of tuples
    มีระบบตรวจสอบและดักจับ Error กรณีไม่มี SP ในระบบ
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
    except pyodbc.Error as e:
        raise DatabaseError(f"ไม่สามารถเชื่อมต่อฐานข้อมูลได้: {str(e)}")

    try:
        if not check_sp_exists(cursor, sp_name):
            raise ObjectNotFoundError(f"ระบบไม่พบฟังก์ชัน (Stored Procedure) '{sp_name}' กรุณารัน setup_procedures.sql เพื่อสร้างฐานข้อมูลให้สมบูรณ์")

        if params:
            placeholders = ', '.join([f'@{k}=?' for k in params.keys()])
            sql = f"EXEC {sp_name} {placeholders}"
            cursor.execute(sql, list(params.values()))
        else:
            cursor.execute(f"EXEC {sp_name}")

        results = []
        while True:
            try:
                rows = cursor.fetchall()
                if rows:
                    results = rows
                    break
            except pyodbc.ProgrammingError:
                pass
            if not cursor.nextset():
                break

        conn.commit()
        return results

    except ObjectNotFoundError as e:
        conn.rollback()
        raise e
    except pyodbc.Error as e:
        conn.rollback()
        err_msg = str(e)
        if "Could not find stored procedure" in err_msg:
            raise ObjectNotFoundError(f"ระบบไม่พบ Stored Procedure '{sp_name}'")
        raise DatabaseError(f"ข้อผิดพลาดจาก SQL Server: {err_msg}")
    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def exec_query(sql, params=None):
    """รัน SQL query ตรงๆ และ return ผลลัพธ์ พร้อมดักจับ View/Table หาย"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
    except pyodbc.Error as e:
        raise DatabaseError(f"ไม่สามารถเชื่อมต่อฐานข้อมูลได้: {str(e)}")

    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()
        return rows
    except pyodbc.Error as e:
        err_msg = str(e)
        if "Invalid object name" in err_msg:
            raise ObjectNotFoundError(f"ระบบไม่พบตารางหรือ View ที่เรียกใช้ กรุณารัน setup_procedures.sql ({err_msg})")
        raise DatabaseError(f"Error executing query: {err_msg}")
    finally:
        cursor.close()
        conn.close()

def get_columns(table_name):
    sql = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ? 
        ORDER BY ORDINAL_POSITION
    """
    rows = exec_query(sql, [table_name])
    return [row[0] for row in rows]

def get_all_tables():
    sql = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """
    rows = exec_query(sql)
    return [row[0] for row in rows]
