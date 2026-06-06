import os
import sys
import django
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

indexes_to_create = [
    ("idx_atleta_pes", "CREATE INDEX idx_atleta_pes ON core_atleta (pes, dni_atleta, nom);"),
    ("idx_se_covering", "CREATE INDEX idx_se_covering ON core_sessioentrenament (data, atleta_id, ubicacio_id);"),
    ("idx_registre_covering", "CREATE INDEX idx_registre_covering ON core_registrediari (atleta_id, data, nivell_energia, nivell_estres);"),
    ("idx_descans_covering", "CREATE INDEX idx_descans_covering ON core_descans (atleta_id, data_inici, duracio);"),
    ("idx_forca_covering", "CREATE INDEX idx_forca_covering ON core_forca (exercici_id, pes, rpe);")
]

def run_query_explain(cursor, weight_filter):
    query = f"""
    EXPLAIN (FORMAT JSON, ANALYZE)
    SELECT 
        a.nom AS nom_atleta,
        u.adreca AS nom_ubicacio,
        COUNT(DISTINCT se.id) AS total_sessions,
        MAX(f.pes) AS pes_maxim_aixecat,
        AVG(f.rpe) AS rpe_mitja,
        AVG(d.duracio) AS mitjana_descans_minuts,
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
        AND a.pes > {weight_filter}
        AND se.data >= '2025-11-14'
    GROUP BY 
        a.dni_atleta, a.nom, u.id, u.adreca
    ORDER BY 
        pes_maxim_aixecat DESC, total_sessions DESC;
    """
    start = time.time()
    cursor.execute(query)
    plan = cursor.fetchone()[0][0]['Plan']
    elapsed = time.time() - start
    
    node_counts = {}
    def extract_node_types(plan_node):
        node_type = plan_node.get('Node Type')
        if node_type:
            node_counts[node_type] = node_counts.get(node_type, 0) + 1
        if 'Plans' in plan_node:
            for child in plan_node['Plans']:
                extract_node_types(child)
    extract_node_types(plan)
    
    return node_counts, plan.get('Actual Total Time'), elapsed

with connection.cursor() as cursor:
    # 1. Clean up potential old indexes
    for name, _ in indexes_to_create:
        try:
            cursor.execute(f"DROP INDEX {name};")
        except Exception:
            pass
    cursor.execute("ANALYZE;")
    
    # 2. Run query BEFORE optimization (Monofil for precision)
    cursor.execute("SET max_parallel_workers_per_gather = 0;")
    print("Running BEFORE optimization...")
    nodes_before, time_before, raw_before = run_query_explain(cursor, 90.0)
    print(f"Nodes: {nodes_before}")
    print(f"Database Actual Time: {time_before:.2f} ms")
    
    # 3. Create indexes
    print("\nCreating indexes...")
    for name, ddl in indexes_to_create:
        cursor.execute(ddl)
    cursor.execute("ANALYZE;")
    
    # 4. Run query AFTER optimization (Shifting weight to 90.01 to ensure cold-cache for new rows)
    print("Running AFTER optimization (shifting weight to 90.01 for cold cache)...")
    nodes_after, time_after, raw_after = run_query_explain(cursor, 90.01)
    print(f"Nodes: {nodes_after}")
    print(f"Database Actual Time: {time_after:.2f} ms")
    
    # 5. Clean up
    print("\nCleaning up indexes...")
    for name, _ in indexes_to_create:
        cursor.execute(f"DROP INDEX {name};")
    cursor.execute("ANALYZE;")
    cursor.execute("RESET max_parallel_workers_per_gather;")
    
    pct_gain = ((time_before - time_after) / time_before) * 100
    print(f"\nTime Before: {time_before:.2f} ms")
    print(f"Time After: {time_after:.2f} ms")
    print(f"Percentage Gain: {pct_gain:.2f}%")
