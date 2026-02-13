from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

handler = Neo4jHandler(**settings['neo4j'])

# Check for researchers
result = handler.execute_cypher('MATCH (r:Researcher) RETURN r.name as name LIMIT 10')
print(f'Researchers found: {len(result)}')
for r in result:
    if r['name']:
        print(f'  - {r["name"]}')

handler.close()
