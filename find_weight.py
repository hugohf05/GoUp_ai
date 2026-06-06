import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT MIN(pes), MAX(pes) FROM core_atleta;")
    min_w, max_w = cursor.fetchone()
    print(f"Weights range: {min_w} to {max_w}")
    cursor.execute("SELECT COUNT(*) FROM core_atleta WHERE pes > 95.0;")
    print(f"Athletes with weight > 95.0: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM core_atleta WHERE pes > 90.0;")
    print(f"Athletes with weight > 90.0: {cursor.fetchone()[0]}")
