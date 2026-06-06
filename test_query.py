import os
import sys
import django
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SET max_parallel_workers_per_gather = 0;")
    
    query = """
    EXPLAIN ANALYZE
    SELECT 
        a.nom AS nom_atleta,
        u.adreca AS nom_ubicacio,
        se.data AS data_sessio,
        se.duracio_total AS duracio_sessio,
        e.nom AS nom_exercici,
        COUNT(f.id) AS total_series_forca,
        MAX(f.pes) AS pes_maxim_aixecat,
        AVG(f.rpe) AS rpe_mitja,
        d.duracio AS descans_minuts,
        rd.nivell_energia AS energia_diaria,
        rd.nivell_estres AS estres_diari
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
    LEFT JOIN 
        core_forca f ON f.exercici_id = e.id
    LEFT JOIN 
        core_registrediari rd ON se.atleta_id = rd.atleta_id AND se.data = rd.data
    LEFT JOIN 
        core_descans d ON se.atleta_id = d.atleta_id AND se.data = CAST(d.data_inici AS date)
    WHERE 
        a.dni_atleta = '00000891H'
        AND u.id = 9903
        AND se.data >= '2025-11-14'
    GROUP BY 
        a.nom, u.adreca, se.data, se.duracio_total, e.id, e.nom, d.duracio, rd.nivell_energia, rd.nivell_estres
    ORDER BY 
        se.data DESC, pes_maxim_aixecat DESC;
    """

    print("Running highly specific query for one athlete and location...")
    try:
        start = time.time()
        cursor.execute(query)
        rows = cursor.fetchall()
        elapsed = time.time() - start
        print(f"Query executed in {elapsed:.4f} seconds.")
        for r in rows[:15]:
            print(r[0])
    except Exception as e:
        print(f"Error: {e}")
