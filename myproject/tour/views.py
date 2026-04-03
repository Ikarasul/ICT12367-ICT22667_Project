import promptpay
import qrcode
import base64
from io import BytesIO

from django.shortcuts import render, redirect

PROMPTPAY_ID = "0632688015"


def tours(request):
    return render(request, 'tours.html', {
        'tours': [],
        'is_logged_in': request.session.get('user_id') is not None,
    })


def login(request):
    error_message = None
    if request.method == 'POST':
        # รับค่าจาก form
        email = request.POST.get('email')
        password = request.POST.get('password')
        # TODO: เชื่อม SQL Server ทีหลัง
        # ตอนนี้ redirect ไปหน้า tours ก่อน
        return redirect('/')
    return render(request, 'login.html', {'error_message': error_message})


def register(request):
    return render(request, 'register.html', {})


def booking(request):
    if request.method == 'POST':
        return redirect('/checkout/')
    schedule_id = request.GET.get('schedule_id', '')
    return render(request, 'booking.html', {
        'schedule_id': schedule_id,
        'tour_name': 'ทัวร์ตัวอย่าง',
        'tour_price': 2500,
        'departure_date': '',
    })


def checkout(request):
    # Collect totals from POST (booking form) or session fallback
    num_adults = int(request.POST.get('num_adults', 1))
    num_children = int(request.POST.get('num_children', 0))
    tour_price = float(request.POST.get('tour_price', 2500))
    tour_name = request.POST.get('tour_name', 'ทัวร์ตัวอย่าง')

    adult_total = num_adults * tour_price
    child_total = num_children * (tour_price * 0.5)
    total_price = adult_total + child_total

    # --- PromptPay QR Code ---
    payload = promptpay.qrcode.generate_payload(PROMPTPAY_ID, total_price)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")
    # --- End PromptPay ---

    return render(request, 'checkout.html', {
        'tour_name': tour_name,
        'num_adults': num_adults,
        'num_children': num_children,
        'adult_total': adult_total,
        'child_total': child_total,
        'total_price': total_price,
        'qr_code': qr_code,
        'promptpay_id': PROMPTPAY_ID,
    })


def dashboard(request):
    return render(request, 'dashboard.html', {
        'bookings': [],
        'schedules': [],
        'revenue': [],
    })


def my_tickets(request):
    return render(request, 'my_tickets.html', {'tickets': []})


def audit_log(request):
    return render(request, 'audit_log.html', {})


def logout_view(request):
    request.session.flush()
    return redirect('/login/')


def crud_list(request, table):
    return render(request, 'admin/table_data.html', {
        'table_name': table,
        'columns': [],
        'rows': [],
    })


def crud_create(request, table):
    return render(request, 'admin/table_form.html', {
        'table_name': table,
        'columns': [],
        'row': None,
    })


def crud_edit(request, table, id):
    return render(request, 'admin/table_form.html', {
        'table_name': table,
        'columns': [],
        'row': [],
    })


def crud_delete(request, table, id):
    return redirect(f'/manage/{table}/')


def manage_tables(request):
    tables = ['Customers', 'Bookings', 'TourPackages', 'TourSchedules',
              'Payments', 'FlightTickets', 'Employees', 'Guides',
              'Vehicles', 'Hotels', 'Passengers', 'Reviews', 'AuditLog']
    return render(request, 'admin/table_list.html', {'tables': tables})


# Aliases expected by urls.py
login_view = login
register_view = register
booking_view = booking
checkout_view = checkout
my_tickets_view = my_tickets
dashboard_view = dashboard
audit_log_view = audit_log
manage_tables_view = manage_tables
