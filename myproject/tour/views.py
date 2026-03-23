# tour/views.py
# ═══════════════════════════════════════
# Views เชื่อม SQL Server จริง
# ═══════════════════════════════════════
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .db import exec_sp, exec_query, get_columns, get_all_tables


# ─── Decorator: ต้อง Login ───────────────
def login_required(roles=None):
    """roles: list เช่น ['Admin','Sales'] หรือ None = ทุก role"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.session.get('user_id'):
                return redirect('/login/')
            if roles and request.session.get('user_role') not in roles:
                return render(request, 'forbidden.html', {}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════
# PUBLIC PAGES
# ═══════════════════════════════════════

def tours(request):
    """หน้าหลัก — แสดงทัวร์ทั้งหมดจาก vw_ScheduleAvailability"""
    try:
        tour_list = exec_query("SELECT * FROM vw_ScheduleAvailability")
    except Exception:
        tour_list = []

    return render(request, 'tours.html', {
        'tours': tour_list,
        'is_logged_in': request.session.get('user_id') is not None,
    })


def login_view(request):
    """Login — เช็คพนักงานก่อน ถ้าไม่ใช่เช็คลูกค้า"""
    if request.session.get('user_id'):
        return redirect('/')

    error_message = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            # ลอง Login พนักงานก่อน
            result = exec_sp('sp_Login', {
                'Email': email,
                'PasswordHash': password,
            })

            if result:
                row = result[0]
                request.session['user_id']   = row[0]
                request.session['user_name'] = row[1]
                request.session['user_email'] = row[2]
                request.session['user_role'] = row[3]
                request.session['user_type'] = 'employee'
                return redirect('/dashboard/')

        except Exception:
            pass

        try:
            # ลอง Login ลูกค้า
            result = exec_sp('sp_LoginCustomer', {
                'Email': email,
                'PasswordHash': password,
            })

            if result:
                row = result[0]
                request.session['user_id']   = row[0]
                request.session['user_name'] = row[1]
                request.session['user_role'] = 'Customer'
                request.session['user_type'] = 'customer'
                return redirect('/')

        except Exception:
            pass

        error_message = 'อีเมลหรือรหัสผ่านไม่ถูกต้อง / Invalid email or password'

    return render(request, 'login.html', {'error_message': error_message})


def register_view(request):
    """สมัครสมาชิกลูกค้า"""
    error_message = None
    success_message = None

    if request.method == 'POST':
        try:
            result = exec_sp('sp_RegisterCustomer', {
                'FullName':    request.POST.get('fullname', ''),
                'Email':       request.POST.get('email', ''),
                'Phone':       request.POST.get('phone', ''),
                'Passport':    request.POST.get('passport', ''),
                'DateOfBirth': request.POST.get('dob', ''),
                'Nationality': request.POST.get('nationality', ''),
                'Address':     request.POST.get('address', ''),
                'PasswordHash':request.POST.get('password', ''),
            })
            success_message = 'สมัครสมาชิกสำเร็จ! กรุณา Login'
            return redirect('/login/')

        except Exception as e:
            error_message = f'เกิดข้อผิดพลาด: {str(e)}'

    return render(request, 'register.html', {
        'error_message': error_message,
        'success_message': success_message,
    })


def logout_view(request):
    request.session.flush()
    return redirect('/login/')


# ═══════════════════════════════════════
# CUSTOMER PAGES
# ═══════════════════════════════════════

@login_required()
def booking_view(request):
    """จองทัวร์"""
    schedule_id = request.GET.get('schedule_id', '')
    error_message = None
    success_message = None

    # ดึงข้อมูลทัวร์จาก schedule_id
    tour_info = {}
    if schedule_id:
        try:
            rows = exec_query(
                "SELECT * FROM vw_ScheduleAvailability WHERE ScheduleID = ?",
                [schedule_id]
            )
            if rows:
                r = rows[0]
                tour_info = {
                    'tour_name':       r[1],
                    'destination':     r[2],
                    'departure_date':  r[3],
                    'return_date':     r[4],
                    'available_seats': r[6],
                    'tour_price':      r[7] if len(r) > 7 else 0,
                    'guide_name':      r[9] if len(r) > 9 else '',
                }
        except Exception:
            pass

    if request.method == 'POST':
        try:
            result = exec_sp('sp_CreateBooking', {
                'CustomerID':  request.session.get('user_id'),
                'ScheduleID':  request.POST.get('schedule_id'),
                'NumAdults':   request.POST.get('num_adults', 1),
                'NumChildren': request.POST.get('num_children', 0),
            })
            # บันทึก AuditLog
            try:
                exec_sp('sp_WriteAuditLog', {
                    'TableName':  'Bookings',
                    'Action':     'INSERT',
                    'PerformedBy': request.session.get('user_id'),
                    'Details':    f"New booking for schedule {request.POST.get('schedule_id')}",
                })
            except Exception:
                pass

            # ส่งอีเมลยืนยันการจอง (Email Confirmation)
            try:
                contact_email = request.POST.get('contact_email')
                if contact_email:
                    subject = f"ยืนยันการจองทัวร์ #{request.POST.get('schedule_id')} - TourCompanyDB"
                    message = (
                        f"ขอบคุณที่จองทัวร์กับเรา!\n\n"
                        f"รายละเอียดการจอง:\n"
                        f"- รหัสตารางทัวร์: {request.POST.get('schedule_id')}\n"
                        f"- จำนวนผู้ใหญ่: {request.POST.get('num_adults')}\n"
                        f"- จำนวนเด็ก: {request.POST.get('num_children')}\n\n"
                        f"คุณสามารถตรวจสอบสถานะการจองได้ที่เมนู 'ตั๋วของฉัน'\n"
                        f"ขอบคุณที่ใช้บริการครับ"
                    )
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [contact_email],
                        fail_silently=True
                    )
            except Exception:
                pass

            return redirect('/my-tickets/')

        except Exception as e:
            print(f"Booking Error: {str(e)}")
            error_message = f'เกิดข้อผิดพลาด: {str(e)}'

    return render(request, 'booking.html', {
        'schedule_id':    schedule_id,
        'error_message':  error_message,
        **tour_info,
    })


@login_required()
def my_tickets_view(request):
    """ตั๋วของฉัน"""
    try:
        tickets = exec_query(
            "SELECT * FROM vw_FlightTickets WHERE CustomerID = ?",
            [request.session.get('user_id')]
        )
    except Exception:
        try:
            tickets = exec_query("SELECT * FROM vw_FlightTickets")
        except Exception:
            tickets = []

    return render(request, 'my_tickets.html', {'tickets': tickets})


# ═══════════════════════════════════════
# STAFF PAGES
# ═══════════════════════════════════════

@login_required(roles=['Admin', 'Sales', 'Accounting'])
def dashboard_view(request):
    """Dashboard พนักงาน"""
    bookings  = []
    schedules = []
    revenue   = []

    try:
        bookings = exec_query("SELECT * FROM vw_BookingSummary")
    except Exception:
        pass

    try:
        schedules = exec_query("SELECT * FROM vw_ScheduleAvailability")
    except Exception:
        pass

    role = request.session.get('user_role')
    if role in ['Admin', 'Accounting']:
        try:
            revenue = exec_query("SELECT * FROM vw_PackageRevenue")
        except Exception:
            pass

    return render(request, 'dashboard.html', {
        'bookings':  bookings,
        'schedules': schedules,
        'revenue':   revenue,
    })


@login_required(roles=['Admin'])
def audit_log_view(request):
    """Audit Log — Admin เท่านั้น"""
    try:
        logs = exec_query("SELECT * FROM vw_AuditLog ORDER BY CreatedAt DESC")
    except Exception:
        logs = []
    return render(request, 'audit_log.html', {'logs': logs})


# ═══════════════════════════════════════
# ADMIN CRUD
# ═══════════════════════════════════════

@login_required(roles=['Admin'])
def manage_tables_view(request):
    """รายชื่อตารางทั้งหมด"""
    try:
        tables = get_all_tables()
    except Exception:
        tables = [
            'Customers', 'Employees', 'TourPackages', 'TourSchedules',
            'Bookings', 'Passengers', 'Payments', 'FlightTickets',
            'Hotels', 'Guides', 'Vehicles', 'Reviews', 'AuditLog',
        ]
    return render(request, 'admin/table_list.html', {'tables': tables})


@login_required(roles=['Admin'])
def crud_list(request, table):
    """แสดงข้อมูลในตาราง"""
    try:
        columns = get_columns(table)
        rows    = exec_query(f"SELECT TOP 100 * FROM [{table}]")
    except Exception as e:
        columns = []
        rows    = []
    return render(request, 'admin/table_data.html', {
        'table_name': table,
        'columns':    columns,
        'rows':       rows,
    })


@login_required(roles=['Admin'])
def crud_create(request, table):
    """เพิ่มข้อมูลในตาราง"""
    try:
        columns = get_columns(table)
        # ตัด column แรก (Primary Key) ออก
        columns = columns[1:]
    except Exception:
        columns = []

    if request.method == 'POST':
        try:
            cols   = ', '.join([f'[{c}]' for c in columns])
            vals   = ', '.join(['?' for _ in columns])
            values = [request.POST.get(c, '') for c in columns]
            exec_query(f"INSERT INTO [{table}] ({cols}) VALUES ({vals})", values)

            # AuditLog
            try:
                exec_sp('sp_WriteAuditLog', {
                    'TableName':   table,
                    'Action':      'INSERT',
                    'PerformedBy': request.session.get('user_id'),
                    'Details':     f'Added new record to {table}',
                })
            except Exception:
                pass

            return redirect(f'/manage/{table}/')
        except Exception as e:
            return render(request, 'admin/table_form.html', {
                'table_name':    table,
                'columns':       columns,
                'row':           None,
                'error_message': str(e),
            })

    return render(request, 'admin/table_form.html', {
        'table_name': table,
        'columns':    columns,
        'row':        None,
    })


@login_required(roles=['Admin'])
def crud_edit(request, table, id):
    """แก้ไขข้อมูลในตาราง"""
    try:
        columns = get_columns(table)
        pk_col  = columns[0]
        rows    = exec_query(f"SELECT * FROM [{table}] WHERE [{pk_col}] = ?", [id])
        row     = rows[0] if rows else None
        edit_columns = columns[1:]
    except Exception:
        columns      = []
        edit_columns = []
        pk_col       = 'ID'
        row          = None

    if request.method == 'POST':
        try:
            set_clause = ', '.join([f'[{c}] = ?' for c in edit_columns])
            values     = [request.POST.get(c, '') for c in edit_columns]
            values.append(id)
            exec_query(f"UPDATE [{table}] SET {set_clause} WHERE [{pk_col}] = ?", values)

            # AuditLog
            try:
                exec_sp('sp_WriteAuditLog', {
                    'TableName':   table,
                    'Action':      'UPDATE',
                    'PerformedBy': request.session.get('user_id'),
                    'Details':     f'Updated record {id} in {table}',
                })
            except Exception:
                pass

            return redirect(f'/manage/{table}/')
        except Exception as e:
            return render(request, 'admin/table_form.html', {
                'table_name':    table,
                'columns':       edit_columns,
                'row':           row,
                'error_message': str(e),
            })

    return render(request, 'admin/table_form.html', {
        'table_name': table,
        'columns':    edit_columns,
        'row':        row,
    })


@login_required(roles=['Admin'])
def crud_delete(request, table, id):
    """ลบข้อมูลในตาราง"""
    try:
        columns = get_columns(table)
        pk_col  = columns[0]
        exec_query(f"DELETE FROM [{table}] WHERE [{pk_col}] = ?", [id])

        # AuditLog
        try:
            exec_sp('sp_WriteAuditLog', {
                'TableName':   table,
                'Action':      'DELETE',
                'PerformedBy': request.session.get('user_id'),
                'Details':     f'Deleted record {id} from {table}',
            })
        except Exception:
            pass

    except Exception:
        pass

    return redirect(f'/manage/{table}/')
