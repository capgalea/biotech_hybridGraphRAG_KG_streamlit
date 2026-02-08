from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

h = Neo4jHandler(settings["neo4j"]["uri"], settings["neo4j"]["user"], settings["neo4j"]["password"], settings["neo4j"]["database"])
res = h.execute_cypher("MATCH (g:Grant) WHERE g.application_id = '1185915' RETURN g.application_id as id")
print(f"Found: {res}")
