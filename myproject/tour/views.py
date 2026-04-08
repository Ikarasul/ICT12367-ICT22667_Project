# tour/views.py
# ═══════════════════════════════════════
# Views เชื่อม SQL Server จริง
# ═══════════════════════════════════════
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from .db import exec_sp, exec_query, get_columns, get_all_tables
from .models import Tourpackages, Tourschedules, Customers, Bookings, Payments
import io
import base64
import secrets
import functools


# ─── Decorator: ต้อง Login ───────────────
def login_required(roles=None):
    """roles: list เช่น ['Admin','Sales'] หรือ None = ทุก role"""
    def decorator(view_func):
        @functools.wraps(view_func)
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
    """หน้าหลัก — แสดงทัวร์ทั้งหมดจาก TourPackages (ORM)"""
    NATURE    = ['beach', 'island', 'koh', 'samila', 'เกาะ', 'หาด', 'ทะเล', 'ธรรมชาติ', 'lake', 'ทะเลสาบ']
    CITY      = ['old town', 'เมืองเก่า', 'heritage', 'วัด', 'ประวัติ', 'pattani', 'songkhla', 'สงขลา', 'ปัตตานี']
    LOCAL     = ['hat yai', 'หาดใหญ่', 'ช้อปปิ้ง', 'local', 'market', 'ตลาด', 'seafood', 'ซีฟู้ด', 'border']

    def infer_cat(name, dest):
        combined = f"{name} {dest}".lower()
        if any(k in combined for k in NATURE):  return 'nature'
        if any(k in combined for k in CITY):    return 'city'
        if any(k in combined for k in LOCAL):   return 'local'
        return 'other'

    destination_filter = request.GET.get('destination', '').strip()
    search_q           = request.GET.get('q', '').strip()

    try:
        from django.db.models import Q
        # Songkhla province only — English district/landmark names + Thai equivalents
        qs = Tourpackages.objects.filter(
            Q(destination_en__icontains='Songkhla') |
            Q(destination_en__icontains='Samila')   |
            Q(destination_en__icontains='Hat Yai')  |
            Q(destination_en__icontains='Koh Yor')  |
            Q(destination_en__icontains='Sadao')    |
            Q(destination__icontains='สงขลา')       |
            Q(destination__icontains='หาดใหญ่')     |
            Q(destination__icontains='เกาะยอ')      |
            Q(destination__icontains='สมิหลา')
        ).exclude(
            Q(packagename__icontains='พัทลุง') |
            Q(packagename__icontains='นครศรีธรรมราช') |
            Q(packagename__icontains='ปัตตานี') |
            Q(packagename__icontains='ยะลา') |
            Q(packagename__icontains='นราธิวาส') |
            Q(packagename__icontains='สตูล') |
            Q(destination__icontains='พัทลุง') |
            Q(destination__icontains='นครศรีธรรมราช') |
            Q(destination__icontains='ปัตตานี') |
            Q(destination__icontains='ยะลา') |
            Q(destination__icontains='นราธิวาส') |
            Q(destination__icontains='สตูล')
        ).order_by('packageid')

        # Get unique destinations ONLY from the filtered Songkhla list, BEFORE applying user filters
        destinations = list(
            qs.values_list('destination', flat=True)
            .distinct().order_by('destination')
        )

        if destination_filter:
            qs = qs.filter(Q(destination__icontains=destination_filter) | Q(destination_en__icontains=destination_filter))
        if search_q:
            qs = qs.filter(
                Q(packagename__icontains=search_q) | Q(tourname_en__icontains=search_q) |
                Q(destination__icontains=search_q) | Q(destination_en__icontains=search_q)
            )

        # Annotate each package with its earliest upcoming schedule
        from django.utils import timezone
        today = timezone.now().date()
        tours_raw = list(qs)
        tour_list = []
        for pkg in tours_raw:
            sched = Tourschedules.objects.filter(
                packageid=pkg, departuredate__gte=today
            ).order_by('departuredate').first()
            booked = Bookings.objects.filter(
                scheduleid__packageid=pkg
            ).count() if sched else 0
            seats_left = (sched.totalseats - booked) if sched else None
            tour_list.append({
                'pkg':       pkg,
                'sched':     sched,
                'seats_left': seats_left,
                'cat':       infer_cat(pkg.packagename, pkg.destination),
            })

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'[tours ORM] {e}')
        # Graceful fallback to raw query
        tour_list    = []
        destinations = []

    return render(request, 'tours.html', {
        'tours':              tour_list,
        'is_logged_in':       request.session.get('user_id') is not None,
        'destination_filter': destination_filter,
        'search_q':           search_q,
        'destinations':       destinations,
    })


def tour_detail_view(request, package_id):
    """Tour Detail page with sticky booking widget."""
    from django.utils import timezone
    from django.db import connection

    # ── Fetch the package ──────────────────────────────────────
    try:
        pkg = Tourpackages.objects.get(pk=package_id)
    except Tourpackages.DoesNotExist:
        return render(request, '404.html', status=404)

    # ── All upcoming schedules for this package ────────────────
    today = timezone.now().date()
    schedules = list(
        Tourschedules.objects.filter(packageid=pkg, departuredate__gte=today)
        .select_related('guideid')
        .order_by('departuredate')
    )

    # Seat availability per schedule
    schedule_data = []
    for s in schedules:
        booked = Bookings.objects.filter(scheduleid=s).count()
        left   = s.totalseats - booked
        schedule_data.append({'sched': s, 'seats_left': left, 'booked': booked})

    nearest = schedules[0] if schedules else None

    # ── Fixed time slots ───────────────────────────────────────
    TIME_SLOTS = [
        {'key': 'morning',   'label': 'Morning',   'time': '09:00 AM', 'icon': 'wb_sunny'},
        {'key': 'afternoon', 'label': 'Afternoon', 'time': '01:00 PM', 'icon': 'partly_cloudy_day'},
        {'key': 'sunset',    'label': 'Sunset',    'time': '04:00 PM', 'icon': 'wb_twilight'},
    ]

    error_msg   = None
    success_msg = None

    # ── POST: Create booking ───────────────────────────────────
    if request.method == 'POST':
        full_name     = request.POST.get('full_name', '').strip()
        email         = request.POST.get('email', '').strip().lower()
        phone         = request.POST.get('phone', '').strip()
        travel_date   = request.POST.get('travel_date', '').strip()
        time_slot     = request.POST.get('time_slot', 'morning')
        num_adults    = int(request.POST.get('num_adults', 1))
        num_children  = int(request.POST.get('num_children', 0))
        accommodation = request.POST.get('accommodation', '').strip()
        guide_name    = request.POST.get('guide_name', '').strip()

        # Basic validation
        if not full_name or not email or not travel_date:
            error_msg = 'กรุณากรอกชื่อ อีเมล และเลือกวันที่เดินทาง / Please fill name, email and select a date.'
        else:
            try:
                # ── Dynamic Schedule Resolution ─────────────────────────────
                from datetime import datetime
                from datetime import timedelta
                parsed_date = datetime.strptime(travel_date, '%Y-%m-%d').date()
                
                selected_sched = Tourschedules.objects.filter(packageid=pkg, departuredate=parsed_date).first()
                if not selected_sched:
                    return_date = parsed_date + timedelta(days=max(0, (pkg.durationdays or 1) - 1))
                    selected_sched = Tourschedules.objects.create(
                        packageid=pkg,
                        departuredate=parsed_date,
                        returndate=return_date,
                        totalseats=40
                    )

                # ── Upsert Customer ─────────────────────────────
                existing = Customers.objects.filter(email=email).first()
                if existing:
                    existing.fullname = full_name
                    if phone: existing.phone = phone
                    existing.save(update_fields=['fullname', 'phone'])
                    customer = existing
                else:
                    from django.contrib.auth.hashers import make_password as _mkpw
                    import secrets as _sec
                    tmp_pw = _mkpw(_sec.token_urlsafe(16))
                    customer = Customers.objects.create(
                        fullname=full_name,
                        email=email,
                        phone=phone,
                        nationality='Thai',
                        passwordhash=tmp_pw,
                        createddate=timezone.now(),
                    )

                # ── Create Booking ──────────────────────────────
                # Store time_slot in the notes via a raw INSERT so we can
                # pass extra_params alongside the ORM-managed fields.
                # Bookings table: BookingID,CustomerID,ScheduleID,NumAdults,NumChildren,BookingDate,Status
                booking = Bookings.objects.create(
                    customerid=customer,
                    scheduleid=selected_sched,
                    numadults=num_adults,
                    numchildren=num_children,
                    bookingdate=timezone.now(),
                    status='Pending',
                )

                # ── Pending Payment record ──────────────────────
                price_adult = float(pkg.priceperperson)
                price_child = price_adult * 0.5
                total = (num_adults * price_adult) + (num_children * price_child)
                Payments.objects.create(
                    bookingid=booking,
                    amount=total,
                    paymentdate=timezone.now(),
                    paymentmethod=None,
                    status='Pending',
                )

                # Store extras in session — displayed on ticket (Bookings table has no extra columns)
                request.session[f'booking_{booking.bookingid}_timeslot']      = time_slot
                request.session[f'booking_{booking.bookingid}_accommodation'] = accommodation
                request.session[f'booking_{booking.bookingid}_guide_name']    = guide_name

                return redirect('payment', booking_id=booking.bookingid)

            except Tourschedules.DoesNotExist:
                error_msg = 'ไม่พบรอบทัวร์ที่เลือก / Selected schedule not found.'
            except Exception as exc:
                import logging
                logging.getLogger(__name__).error(f'[tour_detail POST] {exc}')
                error_msg = f'เกิดข้อผิดพลาด / Error: {exc}'

    # ── Static gallery images (fallback until ImageURL populated) ──
    GALLERY = [
        'https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=900&q=80',
        'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=900&q=80',
        'https://images.unsplash.com/photo-1501854140801-50d01698950b?w=900&q=80',
        'https://images.unsplash.com/photo-1519046904884-53103b34b206?w=900&q=80',
    ]
    gallery_imgs = [pkg.imageurl] + GALLERY if pkg.imageurl else GALLERY

    days = pkg.durationdays or 1
    itinerary_days = list(range(1, min(days, 5) + 1))

    return render(request, 'tour_detail.html', {
        'pkg':            pkg,
        'schedules':      schedule_data,
        'nearest':        nearest,
        'time_slots':     TIME_SLOTS,
        'error_msg':      error_msg,
        'success_msg':    success_msg,
        'is_logged_in':   request.session.get('user_id') is not None,
        'user_name':      request.session.get('user_name', ''),
        'user_email':     request.session.get('user_email', ''),
        'gallery_imgs':   gallery_imgs,
        'itinerary_days': itinerary_days,
    })



def change_language(request, lang_code):
    # บันทึกภาษาลง Session
    request.session['django_language'] = lang_code
    # รีเฟรชกลับไปหน้าเดิมที่เพิ่งกดมา
    return redirect(request.META.get('HTTP_REFERER', '/'))


def login_view(request):
    """Login — เช็คพนักงานก่อน ถ้าไม่ใช่เช็คลูกค้า"""
    if request.session.get('user_id'):
        return redirect('/')

    error_message = None

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            error_message = 'กรุณากรอกอีเมลและรหัสผ่าน / Please enter email and password'
            return render(request, 'login.html', {'error_message': error_message})

        # ลอง Login พนักงานก่อน (employees ใช้ plain hash ใน DB)
        try:
            result = exec_sp('sp_Login', {
                'Email':        email,
                'PasswordHash': password,
            })
            if result:
                row = result[0]
                request.session['user_id']    = row[0]
                request.session['user_name']  = row[1]
                request.session['user_email'] = row[2]
                request.session['user_role']  = row[3]
                request.session['user_type']  = 'employee'
                return redirect('/dashboard/')
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f'[login] employee SP error: {e}')

        # ลอง Login ลูกค้า — ดึง hash จาก DB แล้ว check_password() ใน Python
        try:
            rows = exec_query(
                "SELECT CustomerID, FullName, PasswordHash FROM Customers WHERE LOWER(Email) = ?",
                [email]
            )
            if rows:
                row         = rows[0]
                stored_hash = row[2]
                if stored_hash and check_password(password, stored_hash):
                    request.session['user_id']    = row[0]
                    request.session['user_name']  = row[1]
                    request.session['user_role']  = 'Customer'
                    request.session['user_type']  = 'customer'
                    request.session['user_email'] = email
                    return redirect('/')
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'[login] customer query error: {e}')
            error_message = 'เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล กรุณาลองใหม่อีกครั้ง'
            return render(request, 'login.html', {'error_message': error_message})

        error_message = 'อีเมลหรือรหัสผ่านไม่ถูกต้อง / Invalid email or password'

    return render(request, 'login.html', {'error_message': error_message})


def dev_setup_view(request):
    """DEV ONLY — สร้าง test account ผ่าน browser โดยไม่ต้องรัน script"""
    from django.http import HttpResponse
    TEST_EMAIL = 'test@toursongkhla.com'
    TEST_PASS  = 'test1234'
    try:
        existing = exec_query("SELECT CustomerID FROM Customers WHERE LOWER(Email) = ?", [TEST_EMAIL])
        if existing:
            exec_query("DELETE FROM Customers WHERE LOWER(Email) = ?", [TEST_EMAIL])
        hashed = make_password(TEST_PASS)
        exec_query(
            "INSERT INTO Customers (FullName, Email, Phone, Nationality, PasswordHash) VALUES (?,?,?,?,?)",
            ['ทดสอบ ระบบ', TEST_EMAIL, '0800000001', 'Thai', hashed]
        )
        cust = exec_query("SELECT CustomerID FROM Customers WHERE LOWER(Email) = ?", [TEST_EMAIL])
        cid  = cust[0][0] if cust else '?'

        # สร้าง test tour ราคา 1 บาท
        exec_query("DELETE FROM TourPackages WHERE PackageName = ?", ['[TEST] ทัวร์ทดสอบ QR 1 บาท'])
        exec_query(
            "INSERT INTO TourPackages (PackageName, Destination, DurationDays, PricePerPerson, Description) VALUES (?,?,?,?,?)",
            ['[TEST] ทัวร์ทดสอบ QR 1 บาท', 'สงขลา (Test)', 1, 1, 'ทดสอบระบบ PromptPay QR']
        )
        pkg = exec_query("SELECT PackageID FROM TourPackages WHERE PackageName = ?", ['[TEST] ทัวร์ทดสอบ QR 1 บาท'])
        pid = pkg[0][0] if pkg else None
        if pid:
            exec_query("DELETE FROM TourSchedules WHERE PackageID = ?", [pid])
            exec_query(
                "INSERT INTO TourSchedules (PackageID, DepartureDate, ReturnDate, TotalSeats) VALUES (?, DATEADD(day,1,CAST(GETDATE() AS DATE)), DATEADD(day,2,CAST(GETDATE() AS DATE)), 10)",
                [pid]
            )

        html = f"""
        <html><head><meta charset="utf-8">
        <style>body{{font-family:sans-serif;max-width:500px;margin:60px auto;padding:20px}}
        .box{{background:#f0fdf4;border:2px solid #16a34a;border-radius:12px;padding:24px}}
        h2{{color:#16a34a}}table{{width:100%;border-collapse:collapse;margin:16px 0}}
        td{{padding:8px 12px;border-bottom:1px solid #ddd}}td:first-child{{color:#666;width:40%}}
        a{{display:inline-block;margin-top:16px;background:#0d9488;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none}}</style>
        </head><body>
        <div class="box">
        <h2>✓ สร้าง Test Account สำเร็จ!</h2>
        <table>
        <tr><td>CustomerID</td><td><b>{cid}</b></td></tr>
        <tr><td>Email</td><td><b>{TEST_EMAIL}</b></td></tr>
        <tr><td>Password</td><td><b>{TEST_PASS}</b></td></tr>
        <tr><td>ทัวร์ทดสอบ</td><td><b>ราคา ฿1 (PackageID: {pid})</b></td></tr>
        </table>
        <a href="/login/">ไป Login &rarr;</a>
        </div></body></html>
        """
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f'<pre style="color:red">Error: {e}</pre>', status=500)


def register_view(request):
    """สมัครสมาชิกลูกค้า"""
    error_message   = None
    success_message = None

    if request.method == 'POST':
        try:
            email           = request.POST.get('email', '').strip().lower()
            raw_password    = request.POST.get('password', '')
            hashed_password = make_password(raw_password)

            # Prefix passport number with doc type for clarity (e.g. "ID:1234..." or "PP:A123...")
            doc_type   = request.POST.get('doc_type', 'passport')
            passport   = request.POST.get('passport', '')
            prefix     = 'ID:' if doc_type == 'thid' else 'PP:'
            passport_val = f"{prefix}{passport}" if passport else ''

            exec_sp('sp_RegisterCustomer', {
                'FullName':    request.POST.get('fullname', ''),
                'Email':       email,
                'Phone':       request.POST.get('phone', ''),
                'Passport':    passport_val,
                'DateOfBirth': request.POST.get('dob', ''),
                'Nationality': request.POST.get('nationality', ''),
                'Address':     request.POST.get('address', ''),
                'PasswordHash': hashed_password,
            })
            return redirect('/login/')

        except Exception as e:
            error_message = f'เกิดข้อผิดพลาด: {str(e)}'

    return render(request, 'register.html', {
        'error_message':   error_message,
        'success_message': success_message,
    })


def logout_view(request):
    request.session.flush()
    return redirect('/login/')


def forgot_password_view(request):
    """Step 1 — ลูกค้ากรอก email เพื่อรีเซ็ตรหัสผ่าน"""
    smtp_error = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        rows = exec_query(
            "SELECT CustomerID, FullName FROM Customers WHERE LOWER(Email) = ?",
            [email]
        )
        if rows:
            token = secrets.token_urlsafe(32)
            request.session['pwd_reset_token'] = token
            request.session['pwd_reset_email'] = email

            reset_url = request.build_absolute_uri(f'/reset-password/?token={token}')

            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings as dj_settings

            customer_name = rows[0][1]

            # ── plain text — ASCII subject, UTF-8 body ───────────
            plain = (
                f"Hello {customer_name},\n\n"
                f"Click the link below to reset your TourSongkhla password:\n"
                f"{reset_url}\n\n"
                f"This link can only be used once.\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"-- TourSongkhla"
            )
            html = (
                f'<html><head><meta charset="utf-8"></head><body>'
                f'<div style="font-family:sans-serif;max-width:520px;margin:auto">'
                f'<div style="background:#0d9488;color:#fff;padding:24px 32px;border-radius:14px 14px 0 0">'
                f'<h2 style="margin:0">TourSongkhla - Password Reset</h2></div>'
                f'<div style="background:#fff;border:1px solid #e2e8f0;padding:32px;border-radius:0 0 14px 14px">'
                f'<p>Hello <strong>{customer_name}</strong>,</p>'
                f'<p>Click the button below to set a new password:</p>'
                f'<p style="text-align:center;margin:28px 0">'
                f'<a href="{reset_url}" style="background:#0d9488;color:#fff;padding:14px 32px;'
                f'border-radius:99px;text-decoration:none;font-weight:700;font-size:15px">'
                f'Reset Password</a></p>'
                f'<p style="color:#94a3b8;font-size:12px">This link can only be used once. '
                f'If you did not request this, please ignore this email.</p>'
                f'</div></div>'
                f'</body></html>'
            )

            try:
                msg = EmailMultiAlternatives(
                    subject='TourSongkhla - Password Reset',   # ASCII only
                    body=plain,
                    from_email=dj_settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                msg.encoding = 'utf-8'                         # ← บังคับ UTF-8
                msg.attach_alternative(html, 'text/html')
                msg.send(fail_silently=False)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'[forgot_password] email error: {e}')
                smtp_error = str(e)

        if smtp_error:
            return render(request, 'forgot_password.html', {
                'sent': False, 'smtp_error': smtp_error
            })
        return render(request, 'forgot_password.html', {'sent': True, 'email': email})

    return render(request, 'forgot_password.html', {'sent': False})


def reset_password_view(request):
    """Step 2 — ลูกค้าตั้งรหัสผ่านใหม่ (ต้องมี session token จาก forgot_password_view)"""
    token_in_url     = request.GET.get('token') or request.POST.get('token', '')
    token_in_session = request.session.get('pwd_reset_token', '')
    email            = request.session.get('pwd_reset_email', '')

    # ตรวจ token — ต้องตรงกัน และต้องมี email
    if not token_in_url or not token_in_session or token_in_url != token_in_session or not email:
        return render(request, 'reset_password.html', {'invalid': True})

    error_message = None

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            error_message = 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร / Password must be at least 8 characters'
        elif password1 != password2:
            error_message = 'รหัสผ่านไม่ตรงกัน / Passwords do not match'
        else:
            new_hash = make_password(password1)
            exec_query(
                "UPDATE Customers SET PasswordHash = ? WHERE Email = ?",
                [new_hash, email]
            )
            # ล้าง session token ทิ้ง
            del request.session['pwd_reset_token']
            del request.session['pwd_reset_email']
            return render(request, 'reset_password.html', {'success': True})

    return render(request, 'reset_password.html', {
        'token': token_in_url,
        'error_message': error_message,
    })


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
                        settings.DEFAULT_FROM_EMAIL,
                        [contact_email],
                        fail_silently=True
                    )
            except Exception:
                pass

            # Redirect to checkout page with the new booking ID
            try:
                new_booking_id = int(result[0][0]) if result and result[0] else None
            except Exception:
                new_booking_id = None
            if new_booking_id:
                return redirect('checkout', booking_id=new_booking_id)
            return redirect('my_tickets')

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
    """ตั๋วของฉัน — แสดงเฉพาะ booking ของ customer ที่ login อยู่"""
    user_id       = request.session.get('user_id')
    tickets       = []
    error_message = None

    try:
        rows = exec_query(
            """SELECT
                   b.BookingID,
                   b.CustomerID,
                   c.FullName                                          AS CustomerName,
                   ISNULL(tp.TourName_en, tp.PackageName)             AS TourName,
                   ISNULL(tp.Destination_en, tp.Destination)          AS Destination,
                   s.DepartureDate,
                   s.ReturnDate,
                   b.Status,
                   b.NumAdults,
                   b.NumChildren,
                   CAST(
                       b.NumAdults   * tp.PricePerPerson
                     + b.NumChildren * (tp.PricePerPerson * 0.5)
                   AS DECIMAL(12,2))                                   AS TotalPrice,
                   tp.PricePerPerson
               FROM  Bookings      b
               JOIN  Customers     c  ON b.CustomerID = c.CustomerID
               JOIN  TourSchedules s  ON b.ScheduleID = s.ScheduleID
               JOIN  TourPackages  tp ON s.PackageID  = tp.PackageID
               WHERE b.CustomerID = ?
               ORDER BY b.BookingID DESC""",
            [user_id]
        )
        tickets = [
            {
                'booking_id':    r[0],
                'customer_id':   r[1],
                'customer_name': r[2],
                'tour_name':     r[3],
                'destination':   r[4],
                'departure':     r[5],
                'return_date':   r[6],
                'status':        r[7],
                'adults':        r[8],
                'children':      r[9],
                'total_price':   r[10],
                'price_pp':      r[11],
            }
            for r in rows
        ]
    except Exception as e:
        error_message = str(e)

    return render(request, 'my_tickets.html', {
        'tickets':       tickets,
        'error_message': error_message,
        'user_name':     request.session.get('user_name', ''),
        'user_email':    request.session.get('user_email', ''),
    })


@login_required()
def pay_later_view(request, booking_id):
    """ลูกค้าเลือก 'ชำระภายหลัง' — อัปเดต status เป็น PayLater"""
    from django.contrib import messages as flash
    user_id = request.session.get('user_id')

    if request.method != 'POST':
        return redirect('my_tickets')

    try:
        # ตรวจสอบว่า booking นี้เป็นของลูกค้าที่ login อยู่จริง
        rows = exec_query(
            "SELECT BookingID, Status FROM Bookings WHERE BookingID = ? AND CustomerID = ?",
            [booking_id, user_id]
        )
        if not rows:
            flash.error(request, 'ไม่พบรายการจองนี้ / Booking not found')
            return redirect('my_tickets')

        current_status = rows[0][1]
        if current_status != 'Pending':
            flash.warning(request, 'รายการนี้ไม่สามารถเลือกชำระภายหลังได้ / This booking cannot be set to Pay Later')
            return redirect('my_tickets')

        # อัปเดต status → PayLater
        exec_query(
            "UPDATE Bookings SET Status = 'PayLater' WHERE BookingID = ? AND CustomerID = ?",
            [booking_id, user_id]
        )
        # บันทึก AuditLog
        exec_query(
            """INSERT INTO AuditLog (TableName, RecordID, Action, ChangedBy, ChangeDetails)
               VALUES ('Bookings', ?, 'UPDATE', ?, 'Status changed to PayLater by customer')""",
            [booking_id, user_id]
        )
        flash.success(
            request,
            f'บันทึกแล้ว! การจอง #TC-{booking_id:06d} จะชำระเงินภายหลัง '
            f'กรุณาชำระภายใน 24 ชั่วโมง / Booking saved. Please pay within 24 hours.'
        )
    except Exception as e:
        flash.error(request, f'เกิดข้อผิดพลาด / Error: {e}')

    return redirect('my_tickets')


# ═══════════════════════════════════════
# STAFF PAGES
# ═══════════════════════════════════════

@login_required(roles=['Admin', 'Sales', 'Accounting'])
def dashboard_view(request):
    """Dashboard พนักงาน"""
    recent_bookings = []
    schedules       = []
    revenue         = []
    stats           = {
        'total_bookings': 0, 
        'total_schedules': 0, 
        'total_revenue': 0,
        'new_customers': 0,
        'pending_payments': 0
    }

    # ยอดรวม
    try:
        rows = exec_query("SELECT * FROM vw_BookingSummary")
        if rows:
            stats['total_bookings'] = rows[0][0]
    except Exception:
        pass

    # ลูกค้าใหม่
    try:
        cus_rows = exec_query("SELECT COUNT(*) FROM Customers")
        if cus_rows:
            stats['new_customers'] = cus_rows[0][0]
    except Exception:
        pass

    # รายการจองล่าสุด 10 รายการ
    try:
        recent_bookings = exec_query(
            "SELECT TOP 10 BookingID, CustomerName, TourName, DepartureDate, Status FROM vw_FlightTickets ORDER BY BookingID DESC"
        )
    except Exception:
        pass

    # ตารางทัวร์
    try:
        schedules = exec_query("SELECT * FROM vw_ScheduleAvailability ORDER BY DepartureDate ASC")
        stats['total_schedules'] = len(schedules)
    except Exception:
        pass

    # รายได้ (Admin/Accounting เท่านั้น)
    role = request.session.get('user_role')
    if role in ['Admin', 'Accounting']:
        try:
            revenue = exec_query("SELECT * FROM vw_PackageRevenue")
            stats['total_revenue'] = sum(int(r[1]) for r in revenue) if revenue else 0
        except Exception:
            pass

    # Audit Log ล่าสุด 5 รายการ (Admin เท่านั้น)
    audit_logs = []
    if role == 'Admin':
        try:
            audit_logs = exec_query("SELECT TOP 5 * FROM vw_AuditLog ORDER BY CreatedAt DESC")
        except Exception:
            pass

    # รายการรอ Approve (PendingReview)
    pending_approvals = []
    try:
        pending_approvals = exec_query(
            """SELECT b.BookingID, c.FullName, tp.PackageName, b.TotalPrice
               FROM Bookings b
               JOIN Customers c  ON b.CustomerID  = c.CustomerID
               JOIN TourSchedules ts ON b.ScheduleID = ts.ScheduleID
               JOIN TourPackages tp  ON ts.PackageID  = tp.PackageID
               WHERE b.Status = 'PendingReview'
               ORDER BY b.BookingID DESC"""
        )
        stats['pending_payments'] = len(pending_approvals)
    except Exception:
        pass

    return render(request, 'dashboard.html', {
        'recent_bookings':  recent_bookings,
        'schedules':        schedules,
        'revenue':          revenue,
        'stats':            stats,
        'audit_logs':       audit_logs,
        'pending_approvals': pending_approvals,
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

# ── Table metadata: maps raw SQL name → friendly UI info ─────────────────────
# css_* fields use full Tailwind class strings so the template never builds
# class names dynamically (Tailwind CDN needs literal strings to detect them).
_TABLE_META = {
    'Bookings': {
        'thai':       'การจองทัวร์',
        'en':         'Tour Bookings',
        'desc':       'รายการจองและสถานะการจองทั้งหมด',
        'icon':       'confirmation_number',
        'css_bar':    'bg-primary',
        'css_icon':   'bg-primary/10 text-primary',
        'css_badge':  'bg-primary/10 text-primary',
        'css_arrow':  'text-primary group-hover:bg-primary group-hover:text-white',
    },
    'Customers': {
        'thai':       'ข้อมูลลูกค้า',
        'en':         'Customers',
        'desc':       'โปรไฟล์และข้อมูลติดต่อลูกค้า',
        'icon':       'people',
        'css_bar':    'bg-sky-400',
        'css_icon':   'bg-sky-100 text-sky-500',
        'css_badge':  'bg-sky-50 text-sky-600',
        'css_arrow':  'text-sky-500 group-hover:bg-sky-500 group-hover:text-white',
    },
    'Employees': {
        'thai':       'ข้อมูลพนักงาน',
        'en':         'Employees',
        'desc':       'บัญชีพนักงานและสิทธิ์การเข้าถึง',
        'icon':       'badge',
        'css_bar':    'bg-violet-400',
        'css_icon':   'bg-violet-100 text-violet-500',
        'css_badge':  'bg-violet-50 text-violet-600',
        'css_arrow':  'text-violet-500 group-hover:bg-violet-500 group-hover:text-white',
    },
    'TourPackages': {
        'thai':       'แพ็กเกจทัวร์',
        'en':         'Tour Packages',
        'desc':       'รายละเอียดและราคาแพ็กเกจทัวร์',
        'icon':       'travel_explore',
        'css_bar':    'bg-secondary',
        'css_icon':   'bg-secondary/10 text-secondary',
        'css_badge':  'bg-secondary/10 text-secondary',
        'css_arrow':  'text-secondary group-hover:bg-secondary group-hover:text-white',
    },
    'TourSchedules': {
        'thai':       'รอบจัดทัวร์',
        'en':         'Tour Schedules',
        'desc':       'วันเดินทางและจำนวนที่นั่งคงเหลือ',
        'icon':       'calendar_month',
        'css_bar':    'bg-teal-400',
        'css_icon':   'bg-teal-100 text-teal-500',
        'css_badge':  'bg-teal-50 text-teal-600',
        'css_arrow':  'text-teal-500 group-hover:bg-teal-500 group-hover:text-white',
    },
    'Payments': {
        'thai':       'ข้อมูลการชำระเงิน',
        'en':         'Payments',
        'desc':       'ประวัติและสถานะการชำระเงิน',
        'icon':       'payments',
        'css_bar':    'bg-emerald-400',
        'css_icon':   'bg-emerald-100 text-emerald-500',
        'css_badge':  'bg-emerald-50 text-emerald-600',
        'css_arrow':  'text-emerald-500 group-hover:bg-emerald-500 group-hover:text-white',
    },
    'Guides': {
        'thai':       'ไกด์นำเที่ยว',
        'en':         'Tour Guides',
        'desc':       'รายชื่อและข้อมูลไกด์ประจำทัวร์',
        'icon':       'record_voice_over',
        'css_bar':    'bg-amber-400',
        'css_icon':   'bg-amber-100 text-amber-500',
        'css_badge':  'bg-amber-50 text-amber-600',
        'css_arrow':  'text-amber-500 group-hover:bg-amber-500 group-hover:text-white',
    },
    'Hotels': {
        'thai':       'โรงแรมที่พัก',
        'en':         'Hotels',
        'desc':       'ที่พักและระดับดาวที่ร่วมรายการ',
        'icon':       'hotel',
        'css_bar':    'bg-rose-400',
        'css_icon':   'bg-rose-100 text-rose-400',
        'css_badge':  'bg-rose-50 text-rose-500',
        'css_arrow':  'text-rose-400 group-hover:bg-rose-400 group-hover:text-white',
    },
    'Vehicles': {
        'thai':       'ยานพาหนะ',
        'en':         'Vehicles',
        'desc':       'รถและพาหนะสำหรับนำเที่ยว',
        'icon':       'directions_bus',
        'css_bar':    'bg-indigo-400',
        'css_icon':   'bg-indigo-100 text-indigo-500',
        'css_badge':  'bg-indigo-50 text-indigo-600',
        'css_arrow':  'text-indigo-500 group-hover:bg-indigo-500 group-hover:text-white',
    },
    'Expenses': {
        'thai':       'บันทึกค่าใช้จ่าย',
        'en':         'Expenses',
        'desc':       'ต้นทุนและค่าใช้จ่ายต่อรอบทัวร์',
        'icon':       'receipt_long',
        'css_bar':    'bg-orange-400',
        'css_icon':   'bg-orange-100 text-orange-500',
        'css_badge':  'bg-orange-50 text-orange-600',
        'css_arrow':  'text-orange-500 group-hover:bg-orange-500 group-hover:text-white',
    },
    'AuditLogs': {
        'thai':       'ประวัติการใช้งาน',
        'en':         'Audit Logs',
        'desc':       'บันทึกการเปลี่ยนแปลงข้อมูลในระบบ',
        'icon':       'manage_search',
        'css_bar':    'bg-slate-400',
        'css_icon':   'bg-slate-100 text-slate-500',
        'css_badge':  'bg-slate-100 text-slate-500',
        'css_arrow':  'text-slate-500 group-hover:bg-slate-500 group-hover:text-white',
    },
}

# Ordered display sequence (most-used tables first)
_TABLE_ORDER = [
    'Bookings', 'Customers', 'TourPackages', 'TourSchedules',
    'Payments', 'Guides', 'Hotels', 'Vehicles', 'Employees',
    'Expenses', 'AuditLogs',
]


@login_required(roles=['Admin'])
def manage_tables_view(request):
    """รายชื่อตารางทั้งหมด — กรองเฉพาะ core tables และแสดงชื่อที่เข้าใจง่าย"""
    # ดึงตารางจริงจาก DB
    try:
        raw_tables = set(get_all_tables())
    except Exception:
        raw_tables = set(_TABLE_META.keys())

    # สร้าง list ตาม _TABLE_ORDER, เฉพาะที่มีอยู่จริงในฐานข้อมูล
    tables = []
    for name in _TABLE_ORDER:
        if name in raw_tables and name in _TABLE_META:
            meta = _TABLE_META[name]
            tables.append({
                'name':       name,          # raw SQL name (ใช้สำหรับ URL)
                'thai':       meta['thai'],
                'en':         meta['en'],
                'desc':       meta['desc'],
                'icon':       meta['icon'],
                'css_bar':    meta['css_bar'],
                'css_icon':   meta['css_icon'],
                'css_badge':  meta['css_badge'],
                'css_arrow':  meta['css_arrow'],
            })

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


# ═══════════════════════════════════════════════════════════════════════════════
# SMART FIELD SYSTEM — FK Dropdowns + Enum Dropdowns for all CRUD forms
# ═══════════════════════════════════════════════════════════════════════════════

# Global FK fields: field_name → SQL returning (id, label)
_FK_QUERIES = {
    'CustomerID': (
        "SELECT CustomerID, FullName + N'  —  ' + Email "
        "FROM Customers ORDER BY FullName",
        False   # not nullable
    ),
    'PerformedBy': (
        "SELECT EmployeeID, FullName + N' (' + Role + N')' "
        "FROM Employees ORDER BY FullName",
        True    # nullable — AuditLogs.PerformedBy can be NULL
    ),
    'ScheduleID': (
        """SELECT s.ScheduleID,
               ISNULL(tp.TourName_en, tp.PackageName)
               + N'  |  ' + CONVERT(NVARCHAR, s.DepartureDate, 105)
               + N'  →  ' + CONVERT(NVARCHAR, s.ReturnDate, 105)
           FROM TourSchedules s
           JOIN TourPackages tp ON s.PackageID = tp.PackageID
           ORDER BY s.DepartureDate ASC""",
        False
    ),
    'PackageID': (
        "SELECT PackageID, ISNULL(TourName_en, PackageName) + N'  (' + Destination + N')' "
        "FROM TourPackages ORDER BY PackageName",
        False
    ),
    'GuideID': (
        "SELECT GuideID, FullName + ISNULL(N'  — ' + Phone, N'') "
        "FROM Guides WHERE IsActive = 1 ORDER BY FullName",
        True    # nullable — TourSchedules.GuideID can be NULL
    ),
    'BookingID': (
        """SELECT b.BookingID,
               N'#' + CAST(b.BookingID AS NVARCHAR)
               + N'  —  ' + c.FullName
               + N'  |  ' + ISNULL(tp.TourName_en, tp.PackageName)
           FROM Bookings b
           JOIN Customers c ON b.CustomerID = c.CustomerID
           JOIN TourSchedules s ON b.ScheduleID = s.ScheduleID
           JOIN TourPackages tp ON s.PackageID = tp.PackageID
           ORDER BY b.BookingID DESC""",
        False
    ),
}

# Enum/Status fields: (TableName, FieldName) → list of (value, label)
_ENUM_CONFIG = {
    # AuditLogs
    ('AuditLogs', 'TableName'): [
        (t, t) for t in ['AuditLogs', 'Bookings', 'Customers', 'Employees',
                          'Guides', 'Hotels', 'Payments', 'TourPackages',
                          'TourSchedules', 'Vehicles']
    ],
    ('AuditLogs', 'Action'): [
        (a, a) for a in ['INSERT', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT']
    ],

    # Bookings
    ('Bookings', 'Status'): [
        ('Pending',       'Pending       — รอดำเนินการ'),
        ('PendingReview', 'PendingReview — รอตรวจสอบ'),
        ('Approved',      'Approved      — อนุมัติแล้ว'),
        ('Confirmed',     'Confirmed     — ยืนยันแล้ว'),
        ('Cancelled',     'Cancelled     — ยกเลิก'),
        ('PayLater',      'PayLater      — ชำระภายหลัง'),
    ],

    # Payments
    ('Payments', 'Status'): [
        ('Pending',   'Pending   — รอชำระ'),
        ('Completed', 'Completed — ชำระแล้ว'),
        ('Failed',    'Failed    — ล้มเหลว'),
        ('Refunded',  'Refunded  — คืนเงิน'),
    ],
    ('Payments', 'PaymentMethod'): [
        ('Cash',          'Cash — เงินสด'),
        ('Credit Card',   'Credit Card — บัตรเครดิต'),
        ('Bank Transfer', 'Bank Transfer — โอนเงิน'),
        ('QR Code',       'QR Code — พร้อมเพย์'),
    ],

    # Employees
    ('Employees', 'Role'): [
        ('Admin',      'Admin'),
        ('Sales',      'Sales'),
        ('Accounting', 'Accounting'),
    ],
    ('Employees', 'IsActive'): [
        ('1', '1  — Active ✓'),
        ('0', '0  — Inactive ✗'),
    ],

    # Guides
    ('Guides', 'IsActive'): [
        ('1', '1  — Active ✓'),
        ('0', '0  — Inactive ✗'),
    ],

    # Hotels
    ('Hotels', 'StarRating'): [
        ('1', '★☆☆☆☆  (1 Star)'),
        ('2', '★★☆☆☆  (2 Stars)'),
        ('3', '★★★☆☆  (3 Stars)'),
        ('4', '★★★★☆  (4 Stars)'),
        ('5', '★★★★★  (5 Stars)'),
    ],
}


def _build_fields(table, columns, row=None, post_data=None):
    """
    สร้าง list of field dicts สำหรับ table_form.html
    แต่ละ field มี: name, value, choices (list of {value,label} หรือ None), nullable
    """
    fields = []
    for i, col in enumerate(columns):
        # ค่าปัจจุบัน (จาก row หรือ POST หรือ ว่าง)
        if post_data:
            value = post_data.get(col, '')
        elif row is not None:
            value = row[i + 1] if i + 1 < len(row) else ''
        else:
            value = ''

        choices  = None
        nullable = False

        # 1. ตรวจ Enum config ก่อน (specific ต่อตาราง)
        enum_key = (table, col)
        if enum_key in _ENUM_CONFIG:
            choices = [{'value': v, 'label': lbl} for v, lbl in _ENUM_CONFIG[enum_key]]

        # 2. ถ้าไม่ใช่ enum ลองดู FK
        elif col in _FK_QUERIES:
            sql, is_nullable = _FK_QUERIES[col]
            nullable = is_nullable
            try:
                rows = exec_query(sql)
                choices = [{'value': r[0], 'label': r[1]} for r in rows]
            except Exception:
                choices = None   # fallback → text input

        fields.append({
            'name':     col,
            'value':    value,
            'choices':  choices,
            'nullable': nullable,
        })
    return fields


def _get_booking_selects():
    """ดึงรายชื่อ Customers + Schedules สำหรับ dropdown ใน Booking form"""
    customers = []
    schedules = []
    try:
        rows = exec_query(
            "SELECT CustomerID, FullName, Email FROM Customers ORDER BY FullName"
        )
        customers = [{'id': r[0], 'label': f"{r[1]} ({r[2]})"} for r in rows]
    except Exception:
        pass
    try:
        rows = exec_query(
            """SELECT
                   s.ScheduleID,
                   ISNULL(tp.TourName_en, tp.PackageName) AS PackageName,
                   s.DepartureDate,
                   s.ReturnDate,
                   (s.TotalSeats - ISNULL(
                       (SELECT SUM(NumAdults + ISNULL(NumChildren,0))
                        FROM Bookings
                        WHERE ScheduleID = s.ScheduleID AND Status != 'Cancelled'), 0)
                   ) AS Available
               FROM TourSchedules s
               JOIN TourPackages tp ON s.PackageID = tp.PackageID
               ORDER BY s.DepartureDate ASC"""
        )
        schedules = [
            {
                'id':        r[0],
                'label':     f"{r[1]}  |  {str(r[2])[:10]}  →  {str(r[3])[:10]}  (ว่าง {r[4]} ที่)",
                'available': r[4],
            }
            for r in rows
        ]
    except Exception:
        pass
    return customers, schedules


@login_required(roles=['Admin'])
def crud_create(request, table):
    """เพิ่มข้อมูลในตาราง"""
    try:
        columns = get_columns(table)
        columns = columns[1:]          # ตัด PK ออก
    except Exception:
        columns = []

    # ─── Bookings: ใช้ template + dropdown พิเศษ ───────────────────────────────
    if table == 'Bookings':
        customers, schedules = _get_booking_selects()
        error_message = None

        if request.method == 'POST':
            try:
                exec_query(
                    """INSERT INTO Bookings
                           (CustomerID, ScheduleID, NumAdults, NumChildren, BookingDate, Status)
                       VALUES (?, ?, ?, ?, GETDATE(), ?)""",
                    [
                        request.POST.get('CustomerID'),
                        request.POST.get('ScheduleID'),
                        request.POST.get('NumAdults', 1),
                        request.POST.get('NumChildren', 0),
                        request.POST.get('Status', 'Pending'),
                    ]
                )
                try:
                    exec_sp('sp_WriteAuditLog', {
                        'TableName':   'Bookings',
                        'Action':      'INSERT',
                        'PerformedBy': request.session.get('user_id'),
                        'Details':     f"Created booking — Customer {request.POST.get('CustomerID')}, Schedule {request.POST.get('ScheduleID')}",
                    })
                except Exception:
                    pass
                return redirect('/manage/Bookings/')
            except Exception as e:
                error_message = str(e)

        return render(request, 'admin/booking_form.html', {
            'table_name':    'Bookings',
            'is_edit':       False,
            'customers':     customers,
            'schedules':     schedules,
            'current':       {},
            'error_message': error_message,
        })
    # ───────────────────────────────────────────────────────────────────────────

    if request.method == 'POST':
        try:
            cols   = ', '.join([f'[{c}]' for c in columns])
            vals   = ', '.join(['?' for _ in columns])
            values = [request.POST.get(c, '') for c in columns]
            exec_query(f"INSERT INTO [{table}] ({cols}) VALUES ({vals})", values)
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
            fields = _build_fields(table, columns, post_data=request.POST)
            return render(request, 'admin/table_form.html', {
                'table_name':    table,
                'fields':        fields,
                'error_message': str(e),
            })

    fields = _build_fields(table, columns)
    return render(request, 'admin/table_form.html', {
        'table_name':    table,
        'fields':        fields,
        'error_message': None,
    })


@login_required(roles=['Admin'])
def crud_edit(request, table, id):
    """แก้ไขข้อมูลในตาราง"""
    try:
        columns      = get_columns(table)
        pk_col       = columns[0]
        rows         = exec_query(f"SELECT * FROM [{table}] WHERE [{pk_col}] = ?", [id])
        row          = rows[0] if rows else None
        edit_columns = columns[1:]
    except Exception:
        columns      = []
        edit_columns = []
        pk_col       = 'ID'
        row          = None

    # ─── Bookings: ใช้ template + dropdown พิเศษ ───────────────────────────────
    if table == 'Bookings':
        customers, schedules = _get_booking_selects()
        error_message = None

        # map row → dict ด้วย column names
        col_names = ['BookingID', 'CustomerID', 'ScheduleID',
                     'NumAdults', 'NumChildren', 'BookingDate', 'Status']
        current = {}
        if row:
            for i, col in enumerate(col_names):
                current[col] = row[i] if i < len(row) else ''

        if request.method == 'POST':
            try:
                exec_query(
                    """UPDATE Bookings SET
                           CustomerID  = ?,
                           ScheduleID  = ?,
                           NumAdults   = ?,
                           NumChildren = ?,
                           Status      = ?
                       WHERE BookingID = ?""",
                    [
                        request.POST.get('CustomerID'),
                        request.POST.get('ScheduleID'),
                        request.POST.get('NumAdults', 1),
                        request.POST.get('NumChildren', 0),
                        request.POST.get('Status', 'Pending'),
                        id,
                    ]
                )
                try:
                    exec_sp('sp_WriteAuditLog', {
                        'TableName':   'Bookings',
                        'Action':      'UPDATE',
                        'PerformedBy': request.session.get('user_id'),
                        'Details':     f'Updated Booking ID {id}',
                    })
                except Exception:
                    pass
                return redirect('/manage/Bookings/')
            except Exception as e:
                error_message = str(e)
                current.update(dict(request.POST))

        return render(request, 'admin/booking_form.html', {
            'table_name':    'Bookings',
            'is_edit':       True,
            'booking_id':    id,
            'customers':     customers,
            'schedules':     schedules,
            'current':       current,
            'error_message': error_message,
        })
    # ───────────────────────────────────────────────────────────────────────────

    if request.method == 'POST':
        try:
            set_clause = ', '.join([f'[{c}] = ?' for c in edit_columns])
            values     = [request.POST.get(c, '') for c in edit_columns]
            values.append(id)
            exec_query(f"UPDATE [{table}] SET {set_clause} WHERE [{pk_col}] = ?", values)
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
            fields = _build_fields(table, edit_columns, post_data=request.POST)
            return render(request, 'admin/table_form.html', {
                'table_name':    table,
                'fields':        fields,
                'is_edit':       True,
                'record_id':     id,
                'error_message': str(e),
            })

    fields = _build_fields(table, edit_columns, row=row)
    return render(request, 'admin/table_form.html', {
        'table_name':    table,
        'fields':        fields,
        'is_edit':       True,
        'record_id':     id,
        'error_message': None,
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


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKOUT  →  PAYMENT  →  PDF TICKET  →  EMAIL
# ═══════════════════════════════════════════════════════════════════════════════

def _fetch_booking_for_ticket(booking_id, user_id):
    """Shared helper: fetch full booking row as dict; returns None if not found."""
    rows = exec_query("""
        SELECT
            b.BookingID, b.CustomerID, c.FullName, c.Email,
            ISNULL(tp.TourName_en, tp.PackageName)          AS TourName,
            ISNULL(tp.Destination_en, tp.Destination)       AS Destination,
            s.DepartureDate, s.ReturnDate, b.Status,
            b.NumAdults, b.NumChildren, tp.PricePerPerson,
            CAST(
                b.NumAdults   * tp.PricePerPerson
              + b.NumChildren * (tp.PricePerPerson * 0.5)
            AS DECIMAL(12,2))                               AS TotalPrice
        FROM  Bookings      b
        JOIN  Customers     c  ON b.CustomerID = c.CustomerID
        JOIN  TourSchedules s  ON b.ScheduleID = s.ScheduleID
        JOIN  TourPackages  tp ON s.PackageID  = tp.PackageID
        WHERE b.BookingID = ? AND b.CustomerID = ?
    """, [booking_id, user_id])

    if not rows:
        return None
    r = rows[0]
    price_pp = float(r[11]) if r[11] else 0
    return {
        'booking_id':     r[0],
        'customer_id':    r[1],
        'customer_name':  r[2],
        'customer_email': r[3],
        'tour_name':      r[4],
        'destination':    r[5],
        'departure':      r[6],
        'return_date':    r[7],
        'status':         r[8],
        'adults':         r[9],
        'children':       r[10],
        'price_pp':       price_pp,
        'total_price':    float(r[12]) if r[12] else 0,
        'adult_total':    float(r[9])  * price_pp,
        'child_total':    float(r[10]) * price_pp * 0.5,
    }


def _send_ticket_email(booking, request=None):
    """
    ส่ง email ยืนยันการจอง พร้อม:
      - HTML body (email_booking.html)
      - Plain text fallback
      - PDF ticket แนบ (xhtml2pdf)
    """
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings as dj_settings
    from io import BytesIO
    try:
        from xhtml2pdf import pisa
    except ImportError:
        pisa = None

    try:
        bid      = booking['booking_id']
        site_url = getattr(dj_settings, 'SITE_URL', 'http://127.0.0.1:8000')

        # สร้าง URL ตั๋ว — ใช้ request.build_absolute_uri ถ้ามี ไม่งั้นใช้ SITE_URL
        if request is not None:
            ticket_url = request.build_absolute_uri(f'/ticket/{bid}/pdf/')
        else:
            ticket_url = f'{site_url}/ticket/{bid}/pdf/'

        # ── Plain text body ──────────────────────────────────────
        plain_text = (
            f'เรียนคุณ {booking["customer_name"]},\n\n'
            f'การชำระเงินของคุณสำเร็จแล้ว!\n\n'
            f'รายละเอียดการจอง #{bid:06d}:\n'
            f'  ทัวร์       : {booking["tour_name"]}\n'
            f'  ปลายทาง    : {booking["destination"]}\n'
            f'  วันเดินทาง : {booking["departure"]}\n'
            f'  วันกลับ    : {booking["return_date"]}\n'
            f'  ผู้ใหญ่    : {booking["adults"]} ท่าน\n'
            f'  เด็ก       : {booking["children"]} ท่าน\n'
            f'  ยอดชำระ    : ฿{booking["total_price"]:,.0f}\n\n'
            f'ดาวน์โหลดตั๋ว: {ticket_url}\n\n'
            f'ขอบคุณที่ใช้บริการ TourSongkhla!'
        )

        # ── HTML body จาก template ───────────────────────────────
        html_body = render_to_string('email_booking.html', {
            'booking':    booking,
            'ticket_url': ticket_url,
            'site_url':   site_url,
        })

        # ── สร้าง EmailMultiAlternatives ─────────────────────────
        msg = EmailMultiAlternatives(
            subject=f'[TourSongkhla] Booking Confirmed #{bid:06d}',  # ASCII only
            body=plain_text,
            from_email=dj_settings.DEFAULT_FROM_EMAIL,
            to=[booking['customer_email']],
        )
        msg.encoding = 'utf-8'                           # ← บังคับ UTF-8
        msg.attach_alternative(html_body, 'text/html')

        # ── แนบ PDF ticket ───────────────────────────────────────
        if pisa is not None:
            pdf_html = render_to_string('ticket_pdf.html', {'booking': booking})
            buf      = BytesIO()
            status   = pisa.CreatePDF(pdf_html, dest=buf)
            if not status.err:
                msg.attach(
                    filename=f'TourTicket_{bid:06d}.pdf',
                    content=buf.getvalue(),
                    mimetype='application/pdf',
                )

        msg.send(fail_silently=True)

    except Exception:
        pass  # Email failure must never break the payment flow


def checkout_view(request, booking_id):
    """Checkout / payment page for a Pending booking."""
    user_id       = request.session.get('user_id')
    error_message = None

    # Try fetching by user_id first; fall back to bare ID lookup
    # (needed when customer just registered during booking flow and session isn't fully set)
    booking = _fetch_booking_for_ticket(booking_id, user_id)
    if not booking:
        # Fallback: try fetching without CustomerID restriction (just issued booking)
        rows = exec_query("""
            SELECT
                b.BookingID, b.CustomerID, c.FullName, c.Email,
                ISNULL(tp.TourName_en, tp.PackageName)          AS TourName,
                ISNULL(tp.Destination_en, tp.Destination)       AS Destination,
                s.DepartureDate, s.ReturnDate, b.Status,
                b.NumAdults, b.NumChildren, tp.PricePerPerson,
                CAST(
                    b.NumAdults   * tp.PricePerPerson
                  + b.NumChildren * (tp.PricePerPerson * 0.5)
                AS DECIMAL(12,2))                               AS TotalPrice
            FROM  Bookings      b
            JOIN  Customers     c  ON b.CustomerID = c.CustomerID
            JOIN  TourSchedules s  ON b.ScheduleID = s.ScheduleID
            JOIN  TourPackages  tp ON s.PackageID  = tp.PackageID
            WHERE b.BookingID = ? AND b.Status = 'Pending'
        """, [booking_id])
        if rows:
            r = rows[0]
            price_pp = float(r[11]) if r[11] else 0
            booking = {
                'booking_id':     r[0], 'customer_id':    r[1],
                'customer_name':  r[2], 'customer_email': r[3],
                'tour_name':      r[4], 'destination':    r[5],
                'departure':      r[6], 'return_date':    r[7],
                'status':         r[8], 'adults':         r[9],
                'children':       r[10], 'price_pp':      price_pp,
                'total_price':    float(r[12]) if r[12] else 0,
                'adult_total':    float(r[9])  * price_pp,
                'child_total':    float(r[10]) * price_pp * 0.5,
            }
    if not booking:
        return redirect('/')

    # Already approved — go straight to ticket download
    if booking['status'] in ('Approved', 'Confirmed'):
        return redirect('download_ticket', booking_id=booking_id)

    if request.method == 'POST':
        try:
            # 1. Mark booking as PendingReview (customer has confirmed payment)
            exec_query(
                "UPDATE Bookings SET Status = 'PendingReview' WHERE BookingID = ?",
                [booking_id]
            )

            # 2. อัปเดต payment record เป็น PendingReview
            exec_query(
                """UPDATE Payments SET PaymentMethod = ?, Status = 'Pending'
                   WHERE BookingID = ?""",
                ['QR Transfer', booking_id]
            )

            # 3. AuditLog
            try:
                exec_sp('sp_WriteAuditLog', {
                    'TableName':   'Payments',
                    'Action':      'UPDATE',
                    'PerformedBy': user_id,
                    'Details':     f'Customer confirmed QR payment for Booking #{booking_id}',
                })
            except Exception:
                pass

            # 4. Redirect directly to ticket page
            return redirect('ticket_view', booking_id=booking_id)

        except Exception as e:
            error_message = str(e)

    # Generate PromptPay QR code from actual booking total
    qr_code_b64 = None
    try:
        import promptpay
        import qrcode as _qrcode
        _phone  = "0632688015"
        _amount = booking['total_price']
        from promptpay import qrcode as _ppqr
        _payload = _ppqr.generate_payload(_phone, _amount)
        _img = _qrcode.make(_payload)
        _buf = io.BytesIO()
        _img.save(_buf, format='PNG')
        qr_code_b64 = base64.b64encode(_buf.getvalue()).decode('utf-8')
    except Exception:
        pass  # Falls back to static QR image in template

    return render(request, 'checkout.html', {
        'booking':       booking,
        'error_message': error_message,
        'qr_code':       qr_code_b64,
        'phone_number':  "0632688015",
    })


def payment_view(request, booking_id):
    """
    New Payment Page — ขั้นตอนที่ 2: ชำระเงิน (Glassmorphism + Mermaid background)
    After booking is created (Pending), customer sees QR + price summary here.
    On confirm → status becomes PendingReview → redirect to ticket page.
    """
    user_id       = request.session.get('user_id')
    error_message = None

    # Fetch booking — try with user first, then by booking_id alone (guest flow)
    booking = _fetch_booking_for_ticket(booking_id, user_id)
    if not booking:
        rows = exec_query("""
            SELECT
                b.BookingID, b.CustomerID, c.FullName, c.Email,
                ISNULL(tp.TourName_en, tp.PackageName)          AS TourName,
                ISNULL(tp.Destination_en, tp.Destination)       AS Destination,
                s.DepartureDate, s.ReturnDate, b.Status,
                b.NumAdults, b.NumChildren, tp.PricePerPerson,
                CAST(
                    b.NumAdults   * tp.PricePerPerson
                  + b.NumChildren * (tp.PricePerPerson * 0.5)
                AS DECIMAL(12,2))                               AS TotalPrice
            FROM  Bookings      b
            JOIN  Customers     c  ON b.CustomerID = c.CustomerID
            JOIN  TourSchedules s  ON b.ScheduleID = s.ScheduleID
            JOIN  TourPackages  tp ON s.PackageID  = tp.PackageID
            WHERE b.BookingID = ? AND b.Status = 'Pending'
        """, [booking_id])
        if rows:
            r = rows[0]
            price_pp = float(r[11]) if r[11] else 0
            booking = {
                'booking_id':     r[0], 'customer_id':    r[1],
                'customer_name':  r[2], 'customer_email': r[3],
                'tour_name':      r[4], 'destination':    r[5],
                'departure':      r[6], 'return_date':    r[7],
                'status':         r[8], 'adults':         r[9],
                'children':       r[10], 'price_pp':      price_pp,
                'total_price':    float(r[12]) if r[12] else 0,
                'adult_total':    float(r[9])  * price_pp,
                'child_total':    float(r[10]) * price_pp * 0.5,
            }
    if not booking:
        return redirect('/')

    # Already approved — show ticket directly
    if booking['status'] in ('Approved', 'Confirmed'):
        return redirect('ticket_view', booking_id=booking_id)

    if request.method == 'POST':
        try:
            # 1. Mark booking as PendingReview (customer confirmed payment)
            exec_query(
                "UPDATE Bookings SET Status = 'PendingReview' WHERE BookingID = ?",
                [booking_id]
            )
            # 2. Update payment record
            exec_query(
                """UPDATE Payments SET PaymentMethod = ?, Status = 'Pending'
                   WHERE BookingID = ?""",
                ['QR Transfer', booking_id]
            )
            # 3. AuditLog
            try:
                exec_sp('sp_WriteAuditLog', {
                    'TableName':   'Payments',
                    'Action':      'UPDATE',
                    'PerformedBy': user_id,
                    'Details':     f'Customer confirmed PromptPay QR payment for Booking #{booking_id}',
                })
            except Exception:
                pass

            # 4. Redirect to ticket page
            return redirect('ticket_view', booking_id=booking_id)

        except Exception as e:
            error_message = str(e)

    # Generate PromptPay QR code
    qr_code_b64 = None
    try:
        import promptpay
        import qrcode as _qrcode
        _phone  = "0632688015"
        _amount = booking['total_price']
        from promptpay import qrcode as _ppqr
        _payload = _ppqr.generate_payload(_phone, _amount)
        _img = _qrcode.make(_payload)
        _buf = io.BytesIO()
        _img.save(_buf, format='PNG')
        qr_code_b64 = base64.b64encode(_buf.getvalue()).decode('utf-8')
    except Exception:
        pass  # Falls back to static QR icon in template

    return render(request, 'payment.html', {
        'booking':       booking,
        'error_message': error_message,
        'qr_code':       qr_code_b64,
        'phone_number':  "0632688015",
    })




@login_required()
def payment_submitted_view(request, booking_id):
    """หน้า 'แจ้งชำระเงินแล้ว รอ admin ตรวจสอบ'"""
    user_id = request.session.get('user_id')
    booking = _fetch_booking_for_ticket(booking_id, user_id)
    if not booking:
        return redirect('my_tickets')
    return render(request, 'payment_submitted.html', {'booking': booking})


@login_required(roles=['Admin', 'Sales', 'Manager'])
def approve_booking_view(request, booking_id):
    """Admin อนุมัติ booking — เปลี่ยน status เป็น Confirmed และ generate email"""
    if request.method != 'POST':
        return redirect('dashboard')

    staff_id = request.session.get('user_id')
    try:
        exec_query(
            "UPDATE Bookings SET Status = 'Approved' WHERE BookingID = ? AND Status = 'Pending'",
            [booking_id]
        )
        exec_query(
            "UPDATE Payments SET Status = 'Completed' WHERE BookingID = ?",
            [booking_id]
        )
        try:
            exec_sp('sp_WriteAuditLog', {
                'TableName':   'Bookings',
                'Action':      'UPDATE',
                'PerformedBy': staff_id,
                'Details':     f'Booking #{booking_id} approved by staff — status changed to Confirmed',
            })
        except Exception:
            pass

        # ส่ง email แจ้งลูกค้า
        try:
            booking = _fetch_booking_for_ticket(booking_id, None)
            if booking:
                booking['status'] = 'Approved'
                _send_ticket_email(booking, request=request)
        except Exception:
            pass

    except Exception as e:
        messages.error(request, f'Approve ไม่สำเร็จ: {e}')
        return redirect('dashboard')

    messages.success(request, f'อนุมัติ Booking #TC-{booking_id:06d} เรียบร้อย ลูกค้าสามารถ download ticket ได้แล้ว')
    return redirect('dashboard')


@login_required()
def download_ticket_view(request, booking_id):
    """Generate and stream a PDF tour ticket."""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from io import BytesIO
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return HttpResponse('xhtml2pdf not installed. Run: pip install xhtml2pdf', status=500)

    user_id = request.session.get('user_id')
    booking = _fetch_booking_for_ticket(booking_id, user_id)
    if not booking:
        return redirect('my_tickets')

    # PDF สร้างได้เฉพาะเมื่อ Approved/Confirmed เท่านั้น
    if booking['status'] not in ('Approved', 'Confirmed'):
        messages.warning(request, 'ตั๋วยังไม่ได้รับการอนุมัติ / Ticket not yet approved')
        return redirect('my_tickets')

    # ─── link_callback ───────────────────────────────────────────────────────
    # xhtml2pdf calls this for every url() in CSS (e.g. @font-face src).
    # We must return an absolute filesystem path so it can open the file.
    # Windows-safe: use pathlib, no drive-letter colon confusion.
    import os
    static_root = settings.BASE_DIR / 'static'

    def link_callback(uri, rel):
        """Resolve CSS/HTML resource URIs to absolute filesystem paths."""
        # Strip leading /static/
        if uri.startswith('/static/'):
            path = static_root / uri[len('/static/'):]
        elif uri.startswith('/'):
            path = settings.BASE_DIR / uri.lstrip('/')
        else:
            path = settings.BASE_DIR / uri
        abs_path = str(path.resolve())
        if not os.path.isfile(abs_path):
            return uri  # fallback — let xhtml2pdf handle the error
        return abs_path
    # ─────────────────────────────────────────────────────────────────────────

    html = render_to_string('ticket_pdf.html', {'booking': booking})
    buf  = BytesIO()
    err  = pisa.CreatePDF(html, dest=buf, link_callback=link_callback)
    if err.err:
        return HttpResponse('PDF generation failed.', status=500)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="TourTicket_{booking_id:06d}.pdf"'
    )
    response.write(buf.getvalue())
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFY PAYMENT  (Sales / Admin only)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required(roles=['Admin', 'Sales', 'Manager'])
def verify_payment_view(request, booking_id):
    """
    Sales / Admin ยืนยันการชำระเงิน:
      - เปลี่ยน status จาก PendingReview → Confirmed
      - อัปเดต Payments.Status → Completed
      - บันทึก AuditLog พร้อมชื่อพนักงาน
    """
    if request.method != 'POST':
        return redirect('dashboard')

    staff_id   = request.session.get('user_id')
    staff_name = request.session.get('user_name', 'Staff')

    try:
        # ตรวจสอบ booking ก่อน
        rows = exec_query(
            "SELECT BookingID, Status FROM Bookings WHERE BookingID = ?",
            [booking_id]
        )
        if not rows:
            messages.error(request, f'ไม่พบ Booking #{booking_id}')
            return redirect('dashboard')

        current_status = rows[0][1]
        if current_status not in ('PendingReview', 'Pending'):
            messages.warning(
                request,
                f'Booking #{booking_id} มีสถานะ {current_status} — ไม่สามารถยืนยันได้'
            )
            return redirect('dashboard')

        # อัปเดต Bookings → Confirmed
        exec_query(
            "UPDATE Bookings SET Status = 'Confirmed' WHERE BookingID = ?",
            [booking_id]
        )
        # อัปเดต Payments → Completed
        exec_query(
            "UPDATE Payments SET Status = 'Completed' WHERE BookingID = ?",
            [booking_id]
        )
        # AuditLog
        exec_query(
            """INSERT INTO AuditLog (TableName, Operation, RecordID, ChangedBy, ChangeDescription)
               VALUES ('Bookings', 'UPDATE', ?, ?, ?)""",
            [
                booking_id,
                staff_id,
                f'Verified by {staff_name}',
            ]
        )

        # ส่ง email ยืนยัน (ถ้าทำได้)
        try:
            booking = _fetch_booking_for_ticket(booking_id, None)
            if booking:
                booking['status'] = 'Confirmed'
                _send_ticket_email(booking, request=request)
        except Exception:
            pass

        messages.success(
            request,
            f'✅ ยืนยันการชำระเงิน Booking #TC-{booking_id:06d} เรียบร้อย!'
        )

    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาด: {e}')

    return redirect('dashboard')


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET VIEW  (HTML ticket พร้อม QR + Watermark)
# ═══════════════════════════════════════════════════════════════════════════════

def ticket_view(request, booking_id):
    """
    E-Ticket page — accessible by guests and logged-in users.
    Extends SQL to include Guide name and time_slot from session.
    """
    user_id   = request.session.get('user_id')
    user_role = request.session.get('user_role', '')
    is_staff  = user_role in ('Admin', 'Sales', 'Manager', 'Accounting')

    # Build the rich SQL — LEFT JOIN on Guides so we still get a row even if no guide
    _base_sql = """
        SELECT
            b.BookingID, b.CustomerID, c.FullName, c.Email,
            ISNULL(tp.TourName_en, tp.PackageName)          AS TourName,
            ISNULL(tp.Destination_en, tp.Destination)       AS Destination,
            s.DepartureDate, s.ReturnDate, b.Status,
            b.NumAdults, b.NumChildren, tp.PricePerPerson,
            CAST(
                b.NumAdults   * tp.PricePerPerson
              + b.NumChildren * (tp.PricePerPerson * 0.5)
            AS DECIMAL(12,2))                               AS TotalPrice,
            ISNULL(g.FullName, 'TBA')                       AS GuideName,
            tp.DurationDays,
            c.Phone
        FROM  Bookings      b
        JOIN  Customers     c  ON b.CustomerID = c.CustomerID
        JOIN  TourSchedules s  ON b.ScheduleID = s.ScheduleID
        JOIN  TourPackages  tp ON s.PackageID  = tp.PackageID
        LEFT  JOIN Guides   g  ON s.GuideID    = g.GuideID
    """

    if is_staff:
        rows = exec_query(_base_sql + "WHERE b.BookingID = ?", [booking_id])
    elif user_id:
        rows = exec_query(_base_sql + "WHERE b.BookingID = ? AND b.CustomerID = ?",
                          [booking_id, user_id])
    else:
        # Guest — allow access by BookingID alone (just issued, session not set)
        rows = exec_query(_base_sql + "WHERE b.BookingID = ?", [booking_id])

    if not rows:
        from django.http import HttpResponse
        return HttpResponse(
            '<h2 style="font-family:sans-serif;padding:40px">'
            'Ticket not found. <a href="/">Go home</a></h2>',
            status=404
        )

    r        = rows[0]
    price_pp = float(r[11]) if r[11] else 0
    booking  = {
        'booking_id':     r[0],
        'customer_id':    r[1],
        'customer_name':  r[2],
        'customer_email': r[3],
        'tour_name':      r[4],
        'destination':    r[5],
        'departure':      r[6],
        'return_date':    r[7],
        'status':         r[8],
        'adults':         r[9],
        'children':       r[10],
        'price_pp':       price_pp,
        'total_price':    float(r[12]) if r[12] else 0,
        'adult_total':    float(r[9])  * price_pp,
        'child_total':    float(r[10]) * price_pp * 0.5,
        'guide_name':     r[13] if len(r) > 13 else 'TBA',
        'duration_days':  r[14] if len(r) > 14 else None,
        'customer_phone': r[15] if len(r) > 15 else '',
    }

    # ── Time slot — stored in session right after tour_detail_view POST ────
    TIME_SLOT_LABELS = {
        'morning':   {'label': 'Morning',   'time': '09:00 AM', 'icon': 'wb_sunny'},
        'afternoon': {'label': 'Afternoon', 'time': '01:00 PM', 'icon': 'partly_cloudy_day'},
        'sunset':    {'label': 'Sunset',    'time': '04:00 PM', 'icon': 'wb_twilight'},
    }
    slot_key   = request.session.get(f'booking_{booking_id}_timeslot', 'morning')
    time_slot  = TIME_SLOT_LABELS.get(slot_key, TIME_SLOT_LABELS['morning'])

    # ── Accommodation + guide override from session ────────────────────
    accommodation  = request.session.get(f'booking_{booking_id}_accommodation', '')
    guide_override = request.session.get(f'booking_{booking_id}_guide_name', '')
    # Apply fallback for accommodation display
    days = booking.get('duration_days') or 0
    if not accommodation:
        accommodation = 'Included' if days and days > 1 else 'Day Trip'
    booking['accommodation'] = accommodation
    # Guide override: if user specified one at booking, show that instead
    if guide_override:
        booking['guide_name'] = guide_override

    # ── QR Code (encodes scan-verify URL) ─────────────────────────────────
    qr_b64 = None
    try:
        import qrcode as _qrcode
        verify_url = request.build_absolute_uri(f'/ticket/{booking_id}/verify/')
        _img = _qrcode.make(verify_url)
        _buf = io.BytesIO()
        _img.save(_buf, format='PNG')
        qr_b64 = base64.b64encode(_buf.getvalue()).decode('utf-8')
    except Exception:
        # Fallback: Google Charts QR API (no library needed)
        qr_b64 = None

    is_confirmed = booking['status'] in ('Confirmed', 'Approved')

    return render(request, 'ticket_view.html', {
        'booking':      booking,
        'qr_b64':       qr_b64,
        'is_confirmed': is_confirmed,
        'is_staff':     is_staff,
        'time_slot':    time_slot,
        'verify_url':   request.build_absolute_uri(f'/ticket/{booking_id}/verify/'),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN VERIFY  (หน้าที่เปิดเมื่อ Staff สแกน QR จากตั๋ว)
# ═══════════════════════════════════════════════════════════════════════════════

def scan_verify_view(request, booking_id):
    """
    หน้า Verification Page ที่ฝังอยู่ใน QR:
      - ทุกคนเปิดได้ (ไม่ต้อง login) เพื่อดูรายละเอียด
      - ถ้า Staff login อยู่ → แสดงปุ่ม Approve
      - POST → เรียก verify_payment_view logic (ต้อง login)
    """
    try:
        rows = exec_query("""
            SELECT
                b.BookingID, c.FullName, c.Email,
                ISNULL(tp.TourName_en, tp.PackageName) AS TourName,
                ISNULL(tp.Destination_en, tp.Destination) AS Destination,
                s.DepartureDate, s.ReturnDate, b.Status,
                b.NumAdults, b.NumChildren,
                CAST(
                    b.NumAdults   * tp.PricePerPerson
                  + b.NumChildren * (tp.PricePerPerson * 0.5)
                AS DECIMAL(12,2)) AS TotalPrice
            FROM  Bookings      b
            JOIN  Customers     c  ON b.CustomerID = c.CustomerID
            JOIN  TourSchedules s  ON b.ScheduleID = s.ScheduleID
            JOIN  TourPackages  tp ON s.PackageID  = tp.PackageID
            WHERE b.BookingID = ?
        """, [booking_id])
    except Exception as e:
        return render(request, 'scan_verify.html', {'error': str(e)})

    if not rows:
        return render(request, 'scan_verify.html', {
            'error': f'ไม่พบ Booking #{booking_id}'
        })

    r = rows[0]
    booking = {
        'booking_id':    r[0],
        'customer_name': r[1],
        'customer_email':r[2],
        'tour_name':     r[3],
        'destination':   r[4],
        'departure':     r[5],
        'return_date':   r[6],
        'status':        r[7],
        'adults':        r[8],
        'children':      r[9],
        'total_price':   float(r[10]) if r[10] else 0,
    }

    user_role = request.session.get('user_role', '')
    is_staff  = user_role in ('Admin', 'Sales', 'Manager')

    # Staff กด Approve จากหน้านี้
    if request.method == 'POST' and is_staff:
        return verify_payment_view(request, booking_id)

    return render(request, 'scan_verify.html', {
        'booking':    booking,
        'is_staff':   is_staff,
        'is_confirmed': booking['status'] in ('Confirmed', 'Approved'),
    })

# ═══════════════════════════════════════════════════════════════════════════════
# CANCEL BOOKING 
# ═══════════════════════════════════════════════════════════════════════════════
def cancel_booking_view(request, booking_id):
    """
    (Customer / Guest) ยกเลิกการจอง — marks as Cancelled + AuditLog → redirect to home
    เฉพาะ Pending หรือ PendingReview เท่านั้นที่ยกเลิกได้
    """
    if request.method != 'POST':
        return redirect('/')

    user_id   = request.session.get('user_id')
    user_name = request.session.get('user_name', 'Guest')

    try:
        rows = exec_query(
            "SELECT BookingID, Status, CustomerID FROM Bookings WHERE BookingID = ?",
            [booking_id]
        )
        if not rows:
            return redirect('/')

        current_status      = rows[0][1]
        booking_customer_id = rows[0][2]

        # ถ้าเป็น logged-in customer ตรวจสิทธิ์; guest ข้ามได้ (เพิ่งจองเสร็จ)
        if user_id and booking_customer_id != user_id:
            return redirect('/')

        if current_status not in ('Pending', 'PendingReview'):
            # Already confirmed — cannot cancel; just go home
            return redirect('/')

        # Mark as Cancelled
        exec_query(
            "UPDATE Bookings SET Status = 'Cancelled' WHERE BookingID = ?",
            [booking_id]
        )

        # AuditLog (best effort)
        try:
            exec_query(
                """INSERT INTO AuditLog (TableName, Operation, RecordID, ChangedBy, ChangeDescription)
                   VALUES ('Bookings', 'UPDATE', ?, ?, ?)""",
                [booking_id, user_id, f'Cancelled by customer ({user_name})']
            )
        except Exception:
            pass

    except Exception:
        pass

    return redirect('/')
