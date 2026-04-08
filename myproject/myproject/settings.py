from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-2yepb2=x_9se&ymdnr&=b&j@&d7z^$b$30nuotff2(*=i=(-c&'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tour',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tour.middleware.DatabaseErrorMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'myproject.context_processors.custom_translations',
            ],
            # ลงทะเบียน custom template tag libraries โดยตรง
            'libraries': {
                'tour_filters': 'tour.templatetags.tour_filters',
            },
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# ═══════════════════════════════════════
# DATABASE — SQL Server (pyodbc)
# เปลี่ยน SERVER ให้ตรงกับเครื่องของคุณ
# ═══════════════════════════════════════
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'TourSongkhla',
        'HOST': 'DESKTOP-S27JDCN\\RAVEN',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;Connection Timeout=30;',
        },
    }
}

# SQL Server connection — ใช้ตรงนี้สำหรับ pyodbc โดยตรง
MSSQL_CONFIG = {
    'SERVER': 'DESKTOP-S27JDCN\\RAVEN',   # ← ชื่อ Server บน Desktop
    'DATABASE': 'TourSongkhla',
    'DRIVER': 'ODBC Driver 17 for SQL Server',
    # Windows Authentication (ไม่ต้อง username/password)
    'TRUSTED_CONNECTION': 'yes',
    # ถ้าใช้ SQL Server Authentication ให้ uncomment บรรทัดด้านล่าง
    # 'UID': 'sa',
    # 'PWD': 'your_password',
}

# ═══════════════════════════════════════
# SESSION
# ═══════════════════════════════════════
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_AGE = 86400  # 1 วัน

# ═══════════════════════════════════════
# INTERNATIONALIZATION
# ═══════════════════════════════════════
LANGUAGE_CODE = 'th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('th', _('Thai')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ═══════════════════════════════════════
# EMAIL CONFIGURATION
# ═══════════════════════════════════════
# ─────────────────────────────────────────────────────────────────
# เลือก backend ที่นี่:
#   'console'  → พิมพ์ email ใน terminal (สำหรับ dev)
#   'smtp'     → ส่ง email จริงผ่าน Gmail SMTP
# ─────────────────────────────────────────────────────────────────
_EMAIL_MODE = os.environ.get('EMAIL_MODE', 'console')   # เปลี่ยนใน .env เป็น 'smtp'

if _EMAIL_MODE == 'smtp':
    # ══ Gmail SMTP ═══════════════════════════════════════════════
    # วิธีสร้าง App Password:
    #   1. myaccount.google.com → Security → 2-Step Verification (เปิดก่อน)
    #   2. myaccount.google.com → Security → App passwords
    #   3. สร้าง App password สำหรับ "Mail" → คัดลอก 16 ตัว
    #   4. ใส่ใน .env:  EMAIL_HOST_USER=you@gmail.com
    #                   EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
    # ══════════════════════════════════════════════════════════════
    EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST          = 'smtp.gmail.com'
    EMAIL_PORT          = 587
    EMAIL_USE_TLS       = True
    EMAIL_USE_UTF8      = True   # ← แก้ปัญหา ASCII codec กับภาษาไทย
    EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL  = os.environ.get('EMAIL_HOST_USER', 'noreply@toursongkhla.com')
else:
    # ══ Console backend (dev default) ════════════════════════════
    EMAIL_BACKEND      = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@toursongkhla.com'

# URL ฐานของเว็บ — ใช้สร้าง link ใน email
SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000')

