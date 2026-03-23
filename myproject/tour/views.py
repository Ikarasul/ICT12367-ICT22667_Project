from django.shortcuts import render, redirect

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
    schedule_id = request.GET.get('schedule_id', '')
    return render(request, 'booking.html', {
        'schedule_id': schedule_id,
        'tour_name': 'ทัวร์ตัวอย่าง',
        'tour_price': 2500,
        'departure_date': '',
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
    tables = ['Customers','Bookings','TourPackages','TourSchedules',
              'Payments','FlightTickets','Employees','Guides',
              'Vehicles','Hotels','Passengers','Reviews','AuditLog']
    return render(request, 'admin/table_list.html', {'tables': tables})
