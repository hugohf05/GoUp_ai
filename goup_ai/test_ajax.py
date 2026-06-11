import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.test import Client
c = Client()
try:
    response = c.get('/api/atletes-autocomplete/?q=Pablo')
    print("Status:", response.status_code)
    print("Content:", response.content)
except Exception as e:
    print("Error:", str(e))
