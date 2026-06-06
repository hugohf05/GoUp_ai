import os
import sys
import django
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

# We will test single functional indexes to see which one changes the plan and speeds it up dramatically!
functional_indexes = [
    ("idx_atleta_pes_func", "CREATE INDEX idx_atleta_pes_func ON core_atleta ((pes + 0));"),
    ("idx_ubicacio_upper_func", "CREATE INDEX idx_ubicacio_upper_func ON core_ubicacio (UPPER(tipus_ubicacio));"),
    ("idx_sessio_year_func", "CREATE INDEX idx_sessio_year_func ON core_sessioentrenament ((EXTRACT(YEAR FROM data)));")
]

query = """
SELECT
   a.nom AS nom_atleta,
   u.adreca AS nom_ubicacio,
   COUNT(DISTINCT se.id) AS total_sessions,
   MAX(f.pes) AS pes_maxim_aixecat,
   AVG(f.rpe) AS rpe_mitja
FROM core_atleta a
JOIN core_sessioentrenament se ON a.dni_atleta = se.atleta_id
JOIN core_ubicacio u ON se.ubicacio_id = u.id
JOIN core_sessioentrenament_exercicis see ON se.id = see.sessioentrenament_id
JOIN core_exercici e ON see.exercici_id = e.id
JOIN core_forca f ON f.exercici_id = e.id
WHERE 
   UPPER(u.tipus_ubicacio) = 'INTERIOR'
   AND (a.pes + 0) > 90.0
   AND EXTRACT(YEAR FROM se.data) >= 2025
GROUP BY 
   a.nom, u.adreca
ORDER BY 
   pes_maxim_aixecat DESC;
"""

with connection.cursor() as cursor:
    for name, ddl in functional_indexes:
        print(f"\n--- Testing with single index: {name} ---")
        try:
            cursor.execute(ddl)
            cursor.execute("ANALYZE;")
            
            start = time.time()
            cursor.execute(f"EXPLAIN ANALYZE {query}")
            rows = cursor.fetchall()
            elapsed = time.time() - start
            print(f"Executed in {elapsed:.4f} seconds.")
            
            # Print first 20 lines of explain
            for r in rows[:20]:
                print(r[0])
                
        except Exception as e:
            print(f"Error testing {name}: {e}")
        finally:
            try:
                cursor.execute(f"DROP INDEX {name};")
            except Exception:
                pass
            cursor.execute("ANALYZE;")
