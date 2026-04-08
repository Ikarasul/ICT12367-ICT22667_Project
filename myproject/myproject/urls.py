# myproject/urls.py
from django.urls import path, include
from tour import views

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('lang/<str:lang_code>/', views.change_language, name='change_language'),
    # Public
    path('',                         views.tours,             name='tours'),
    path('tours/',                   views.tours,             name='tours_alias'),
    path('tour/<int:package_id>/',   views.tour_detail_view,  name='tour_detail'),
    path('login/',                   views.login_view,        name='login'),
    path('register/',                views.register_view,     name='register'),
    path('logout/',                  views.logout_view,       name='logout'),

    # Customer
    path('booking/',                          views.booking_view,        name='booking'),
    path('my-tickets/',                       views.my_tickets_view,     name='my_tickets'),
    path('checkout/<int:booking_id>/',              views.checkout_view,          name='checkout'),
    path('checkout/<int:booking_id>/submitted/',    views.payment_submitted_view, name='payment_submitted'),
    path('payment/<int:booking_id>/',              views.payment_view,           name='payment'),
    path('ticket/<int:booking_id>/',               views.ticket_view,            name='ticket_view'),
    path('ticket/<int:booking_id>/pdf/',            views.download_ticket_view,   name='download_ticket'),
    path('ticket/<int:booking_id>/verify/',         views.scan_verify_view,       name='scan_verify'),
    path('booking/<int:booking_id>/approve/',       views.approve_booking_view,   name='approve_booking'),
    path('booking/<int:booking_id>/verify-payment/',views.verify_payment_view,    name='verify_payment'),
    path('booking/<int:booking_id>/cancel/',        views.cancel_booking_view,  name='cancel_booking'),
    path('pay-later/<int:booking_id>/',       views.pay_later_view,      name='pay_later'),

    # Staff
    path('dashboard/',  views.dashboard_view,   name='dashboard'),
    path('audit-log/',  views.audit_log_view,   name='audit_log'),

    # Admin CRUD
    path('manage/',                              views.manage_tables_view, name='manage_tables'),
    path('manage/<str:table>/',                  views.crud_list,          name='crud_list'),
    path('manage/<str:table>/create/',           views.crud_create,        name='crud_create'),
    path('manage/<str:table>/edit/<path:id>/',    views.crud_edit,          name='crud_edit'),
    path('manage/<str:table>/delete/<path:id>/',  views.crud_delete,        name='crud_delete'),

    # Password Reset
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/',  views.reset_password_view,  name='reset_password'),

    # DEV ONLY — สร้าง test account ผ่าน browser
    path('dev-setup/', views.dev_setup_view, name='dev_setup'),
]
