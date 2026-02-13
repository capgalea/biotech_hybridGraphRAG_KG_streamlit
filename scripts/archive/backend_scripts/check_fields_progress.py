from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

h = Neo4jHandler(settings["neo4j"]["uri"], settings["neo4j"]["user"], settings["neo4j"]["password"], settings["neo4j"]["database"])
res = h.execute_cypher("MATCH (g:Grant) WHERE g.field_of_research IS NOT NULL AND g.field_of_research <> '' RETURN count(g) as count")
print(f"Grants with field_of_research: {res[0]['count']}")
res2 = h.execute_cypher("MATCH (g:Grant) WHERE g.grant_type IS NOT NULL AND g.grant_type <> '' RETURN count(g) as count")
print(f"Grants with grant_type: {res2[0]['count']}")
