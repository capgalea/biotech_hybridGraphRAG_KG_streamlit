from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

h = Neo4jHandler(settings["neo4j"]["uri"], settings["neo4j"]["user"], settings["neo4j"]["password"], settings["neo4j"]["database"])
res = h.execute_cypher("MATCH (g:Grant) WHERE g.funding_body IS NOT NULL RETURN count(g) as count")
print(f"Grants with funding body: {res[0]['count']}")
