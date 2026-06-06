import os
import django
import json

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

with connection.cursor() as cursor:
    cursor.execute(query)
    plan = cursor.fetchone()[0]
    
    node_counts = {}
    extract_node_types(plan[0]['Plan'], node_counts)
    
    print("=== INITIAL PLAN ===")
    print(json.dumps(node_counts, indent=2))
    print(f"Total Cost: {plan[0]['Plan']['Total Cost']}")
    print(f"Actual Time: {plan[0]['Plan']['Actual Total Time']}")

