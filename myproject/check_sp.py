import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from tour.db import exec_query

print("--- sp_RegisterCustomer ---")
try:
    cols = exec_query("EXEC sp_helptext 'sp_RegisterCustomer'")
    for c in cols:
        print(c[0].strip())
except Exception as e:
    print(e)
