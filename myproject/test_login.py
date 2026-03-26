import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from tour.db import exec_sp

try:
    print("Testing Employee Login:")
    res1 = exec_sp('sp_Login', {'Email': 'wichai@tour.com', 'PasswordHash': 'hash1234'})
    print(repr(res1))
except Exception as e:
    print(f"Error Employee: {e}")

try:
    print("Testing Customer Login:")
    res2 = exec_sp('sp_LoginCustomer', {'Email': 'john@example.com', 'PasswordHash': 'pass1234'})
    print(repr(res2))
except Exception as e:
    print(f"Error Customer: {e}")
