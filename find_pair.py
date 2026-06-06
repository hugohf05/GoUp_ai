import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
    SELECT se.atleta_id, se.ubicacio_id, COUNT(*) 
    FROM core_sessioentrenament se 
    GROUP BY se.atleta_id, se.ubicacio_id 
    HAVING COUNT(*) >= 3
    LIMIT 5;
    """)
    rows = cursor.fetchall()
    print("Matching athlete and location pairs:")
    for r in rows:
        print(f"DNI: {r[0]} | Location ID: {r[1]} | Count: {r[2]}")
