import os
import sys
import django
import json
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'goup_ai'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from django.db import connection

query = """
EXPLAIN (FORMAT JSON, ANALYZE)
SELECT 
    a.nom AS nom_atleta,
    COUNT(se.id) AS total_sessions,
    MIN(se.duracio_total) AS duracio_minima,
    MAX(se.duracio_total) AS duracio_maxima
FROM 
    core_atleta a
JOIN 
    core_sessioentrenament se ON a.dni_atleta = se.atleta_id
JOIN 
    core_ubicacio u ON se.ubicacio_id = u.id
WHERE 
    u.tipus_ubicacio = 'EXTERIOR' 
    AND a.estat = 'ACTIU'
GROUP BY 
    a.dni_atleta, a.nom
ORDER BY 
    total_sessions DESC;
"""

def extract_node_types(plan_node, node_counts):
    node_type = plan_node.get('Node Type')
    if node_type:
        node_counts[node_type] = node_counts.get(node_type, 0) + 1
    
    if 'Plans' in plan_node:
        for child in plan_node['Plans']:
            extract_node_types(child, node_counts)

def get_plan_info(cursor, query_to_run):
    cursor.execute(query_to_run)
    plan = cursor.fetchone()[0][0]['Plan']
    
    node_counts = {}
    extract_node_types(plan, node_counts)
    
    return {
        'counts': node_counts,
        'cost': plan.get('Total Cost'),
        'time': plan.get('Actual Total Time')
    }

try:
    with connection.cursor() as cursor:
        info_before = get_plan_info(cursor, query)
        
        cursor.execute("SET enable_seqscan = off;")
        cursor.execute("SET enable_hashjoin = off;")
        cursor.execute("CREATE INDEX idx_atleta_estat ON core_atleta(estat, dni_atleta, nom);")
        cursor.execute("CREATE INDEX idx_ubicacio_tipus ON core_ubicacio(tipus_ubicacio, id);")
        cursor.execute("CREATE INDEX idx_se_join ON core_sessioentrenament(ubicacio_id, atleta_id, duracio_total);")
        
        info_after = get_plan_info(cursor, query)
        
        cursor.execute("DROP INDEX idx_atleta_estat;")
        cursor.execute("DROP INDEX idx_ubicacio_tipus;")
        cursor.execute("DROP INDEX idx_se_join;")
        
        print("=== BEFORE ===")
        print(json.dumps(info_before, indent=2))
        print("=== AFTER (Forced) ===")
        print(json.dumps(info_after, indent=2))
        
except Exception as e:
    print(f"Error: {e}")
