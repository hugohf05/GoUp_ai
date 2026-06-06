import os
import sys
import django
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

indexes_to_create = [
    ("idx_se_data_opt", "CREATE INDEX idx_se_data_opt ON core_sessioentrenament (data, atleta_id, ubicacio_id);"),
    ("idx_descans_atleta_datetime", "CREATE INDEX idx_descans_atleta_datetime ON core_descans (atleta_id, data_inici, duracio);"),
    ("idx_registre_opt", "CREATE INDEX idx_registre_opt ON core_registrediari (atleta_id, data, nivell_energia, nivell_estres);"),
    ("idx_forca_ex_pes", "CREATE INDEX idx_forca_ex_pes ON core_forca (exercici_id, pes, rpe);"),
    ("idx_atleta_estat_dni", "CREATE INDEX idx_atleta_estat_dni ON core_atleta (estat, dni_atleta, nom);"),
    ("idx_ubicacio_tipus_id", "CREATE INDEX idx_ubicacio_tipus_id ON core_ubicacio (tipus_ubicacio, id, adreca);")
]

with connection.cursor() as cursor:
    cursor.execute("SET max_parallel_workers_per_gather = 0;")
    
    query = """
    EXPLAIN ANALYZE
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
        AND se.data >= '2025-05-14'
    GROUP BY 
        a.dni_atleta, a.nom, u.id, u.adreca
    ORDER BY 
        pes_maxim_aixecat DESC, total_sessions DESC;
    """

    print("--- CREATING INDEXES ---")
    for name, ddl in indexes_to_create:
        try:
            print(f"Creating {name}...")
            cursor.execute(ddl)
        except Exception as e:
            print(f"Error creating {name}: {e}")
            
    print("\nRunning ANALYZE...")
    cursor.execute("ANALYZE;")

    print("\nRunning single-threaded rewritten query WITH indexes...")
    try:
        start = time.time()
        cursor.execute(query)
        rows = cursor.fetchall()
        elapsed = time.time() - start
        print(f"Query executed in {elapsed:.4f} seconds.")
        for r in rows[:40]:
            print(r[0])
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- DROPPING INDEXES ---")
    for name, _ in indexes_to_create:
        try:
            print(f"Dropping {name}...")
            cursor.execute(f"DROP INDEX {name};")
        except Exception as e:
            print(f"Error dropping {name}: {e}")
            
    cursor.execute("ANALYZE;")
