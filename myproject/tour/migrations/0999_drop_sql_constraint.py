from django.db import migrations


def drop_and_recreate_status_constraint(apps, schema_editor):
    """
    Runs directly against SQL Server via pyodbc — bypasses Django's SQLite
    default database so T-SQL syntax is valid.
    """
    from django.conf import settings
    try:
        import pyodbc
    except ImportError:
        print("  [0999] pyodbc not installed — skipping SQL Server migration.")
        return

    cfg = getattr(settings, 'MSSQL_CONFIG', None)
    if not cfg:
        print("  [0999] MSSQL_CONFIG not found in settings — skipping.")
        return

    # Build connection string
    conn_str = (
        f"DRIVER={{{cfg['DRIVER']}}};"
        f"SERVER={cfg['SERVER']};"
        f"DATABASE={cfg['DATABASE']};"
    )
    if cfg.get('TRUSTED_CONNECTION') == 'yes':
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={cfg['UID']};PWD={cfg['PWD']};"

    try:
        conn = pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        print(f"  [0999] Cannot connect to SQL Server: {e} — skipping.")
        return

    cursor = conn.cursor()

    # 1. Drop any existing status CHECK constraint on Bookings
    cursor.execute("""
        IF EXISTS (
            SELECT 1 FROM sys.check_constraints cc
            JOIN sys.tables t ON cc.parent_object_id = t.object_id
            WHERE t.name = 'Bookings'
              AND cc.name LIKE 'CK%Bookings%Status%'
        )
        BEGIN
            DECLARE @cname NVARCHAR(200)
            SELECT @cname = cc.name
            FROM sys.check_constraints cc
            JOIN sys.tables t ON cc.parent_object_id = t.object_id
            WHERE t.name = 'Bookings'
              AND cc.name LIKE 'CK%Bookings%Status%'
            EXEC('ALTER TABLE Bookings DROP CONSTRAINT [' + @cname + ']')
        END
    """)

    # 2. Add a new permissive constraint that includes all valid statuses
    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM sys.check_constraints cc
            JOIN sys.tables t ON cc.parent_object_id = t.object_id
            WHERE t.name = 'Bookings' AND cc.name = 'CK_Bookings_Status'
        )
        BEGIN
            ALTER TABLE Bookings ADD CONSTRAINT CK_Bookings_Status
            CHECK (Status IN (
                'Pending', 'Approved', 'Confirmed',
                'Cancelled', 'PayLater', 'PendingReview'
            ))
        END
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("  [0999] SQL Server constraint updated successfully.")


class Migration(migrations.Migration):
    dependencies = [('tour', '0001_initial')]

    operations = [
        migrations.RunPython(
            drop_and_recreate_status_constraint,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
