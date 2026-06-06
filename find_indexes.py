import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename = 'core_sessioentrenament_exercicis';
    """)
    for row in cursor.fetchall():
        print(row)
