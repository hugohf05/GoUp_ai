import os
import sys
import django
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

indexes_to_create = [
    ("idx_se_covering", "CREATE INDEX idx_se_covering ON core_sessioentrenament (data, atleta_id, ubicacio_id);"),
    ("idx_atleta_estat", "CREATE INDEX idx_atleta_estat ON core_atleta (estat, dni_atleta, nom);"),
    ("idx_ubicacio_covering", "CREATE INDEX idx_ubicacio_covering ON core_ubicacio (tipus_ubicacio, id, adreca);"),
    ("idx_forca_covering", "CREATE INDEX idx_forca_covering ON core_forca (exercici_id, pes, rpe);"),
    ("idx_registre_covering", "CREATE INDEX idx_registre_covering ON core_registrediari (atleta_id, data, nivell_energia, nivell_estres);"),
    ("idx_descans_covering", "CREATE INDEX idx_descans_covering ON core_descans (atleta_id, data_inici, duracio);")
]

query = """
SELECT 
    a.nom AS nom_atleta,
    u.adreca AS nom_ubicacio,
    COUNT(DISTINCT se.id) AS total_sessions,
    MAX(f.pes) AS pes_maxim_aixecat,
    AVG(f.rpe) AS rpe_mitja,
    AVG(d.duracio) AS mitjana_descans,
    AVG(rd.nivell_energia) AS mitjana_energia,
    AVG(rd.nivell_estres) AS mitjana_estres
FROM 
    core_atleta a
JOIN 
    core_sessioentrenament se ON a.dni_atleta = se.atleta_id
JOIN 
    core_ubicacio u ON se.ubicacio_id = u.id
JOIN 
    core_sessioentrenament_exercicis see ON se.id = see.sessioentrenament_id
JOIN 
    core_exercici e ON see.exercici_id = e.id
JOIN 
    core_forca f ON f.exercici_id = e.id
JOIN 
    core_registrediari rd ON se.atleta_id = rd.atleta_id AND se.data = rd.data
JOIN 
    core_descans d ON se.atleta_id = d.atleta_id 
    AND d.data_inici >= se.data 
    AND d.data_inici < se.data + INTERVAL '1 day'
WHERE 
    u.tipus_ubicacio = 'INTERIOR'
    AND a.estat = 'ACTIU'
    AND se.data >= '2026-05-07'
GROUP BY 
    a.dni_atleta, a.nom, u.id, u.adreca
ORDER BY 
    pes_maxim_aixecat DESC, total_sessions DESC;
"""

with connection.cursor() as cursor:
    # 1. Run WITHOUT indexes
    print("=== RUNNING WITHOUT INDEXES ===")
    cursor.execute("SET max_parallel_workers_per_gather = 0;")
    start = time.time()
    cursor.execute(f"EXPLAIN ANALYZE {query}")
    explain_without = cursor.fetchall()
    time_without_single = time.time() - start
    print(f"Single-threaded without indexes: {time_without_single:.4f} seconds.")
    
    # 2. Create indexes
    print("\n=== CREATING INDEXES ===")
    for name, ddl in indexes_to_create:
        try:
            print(f"Creating {name}...")
            cursor.execute(ddl)
        except Exception as e:
            print(f"Error: {e}")
            
    cursor.execute("ANALYZE;")

    # 3. Run WITH indexes
    print("\n=== RUNNING WITH INDEXES ===")
    cursor.execute("SET max_parallel_workers_per_gather = 0;")
    start = time.time()
    cursor.execute(f"EXPLAIN ANALYZE {query}")
    explain_with_single = cursor.fetchall()
    time_with_single = time.time() - start
    print(f"Single-threaded WITH indexes: {time_with_single:.4f} seconds.")
    
    # Print first 20 lines of optimized query plan
    for r in explain_with_single[:35]:
        print(r[0])

    # 4. Drop indexes
    print("\n=== DROPPING INDEXES ===")
    for name, _ in indexes_to_create:
        try:
            print(f"Dropping {name}...")
            cursor.execute(f"DROP INDEX {name};")
        except Exception as e:
            print(f"Error: {e}")
            
    cursor.execute("ANALYZE;")
