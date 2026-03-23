# myproject/urls.py
from django.urls import path, include
from django.views.generic import RedirectView
from tour import views

urlpatterns = [
    path('lang/<str:lang_code>/', views.change_language, name='change_language'),
    # Public
    path('',            views.tours,           name='tours'),
    path('tours/',      views.tours,           name='tours_alias'),  # alias for /tours/
    path('login/',      views.login_view,       name='login'),
    path('register/',   views.register_view,    name='register'),
    path('logout/',     views.logout_view,      name='logout'),

    # Customer
    path('booking/',    views.booking_view,     name='booking'),
    path('my-tickets/', views.my_tickets_view,  name='my_tickets'),

    # Staff
    path('dashboard/',  views.dashboard_view,   name='dashboard'),
    path('audit-log/',  views.audit_log_view,   name='audit_log'),

    # Admin CRUD
    path('manage/',                              views.manage_tables_view, name='manage_tables'),
    path('manage/<str:table>/',                  views.crud_list,          name='crud_list'),
    path('manage/<str:table>/create/',           views.crud_create,        name='crud_create'),
    path('manage/<str:table>/edit/<int:id>/',    views.crud_edit,          name='crud_edit'),
    path('manage/<str:table>/delete/<int:id>/',  views.crud_delete,        name='crud_delete'),

    # Misc
    path('forgot-password/', RedirectView.as_view(url='/login/'), name='forgot_password'),
]
