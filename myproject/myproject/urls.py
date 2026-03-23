"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from tour import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.tours, name='tours'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('booking/', views.booking, name='booking'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('audit-log/', views.audit_log, name='audit_log'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('logout/', views.logout_view, name='logout'),
    path('manage/', views.manage_tables, name='manage_tables'),
    path('manage/<str:table>/', views.crud_list, name='crud_list'),
    path('manage/<str:table>/create/', views.crud_create, name='crud_create'),
    path('manage/<str:table>/edit/<int:id>/', views.crud_edit, name='crud_edit'),
    path('manage/<str:table>/delete/<int:id>/', views.crud_delete, name='crud_delete'),
]
