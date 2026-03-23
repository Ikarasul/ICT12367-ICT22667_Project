import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from tour.db import exec_sp

print("--- Testing Login ---")
try:
    res = exec_sp('sp_LoginCustomer', {
        'Email': 'somchai@email.com',
        'Password': 'pass1234'
    })
    print("Success:", res)
except Exception as e:
    print("Error:", e)
