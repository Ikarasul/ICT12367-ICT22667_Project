import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from tour.db import exec_query

print("--- sp_Login ---")
try:
    cols = exec_query("EXEC sp_helptext 'sp_Login'")
    for c in cols:
        print(c[0])
except Exception as e:
    print(e)
print("--- sp_LoginCustomer ---")
try:
    cols = exec_query("EXEC sp_helptext 'sp_LoginCustomer'")
    for c in cols:
        print(c[0])
except Exception as e:
    print(e)
print("--- Check Customer Passwords ---")
try:
    cols = exec_query("SELECT Email, PasswordHash FROM Customers")
    for c in cols:
        print(c)
except Exception as e:
    print(e)
