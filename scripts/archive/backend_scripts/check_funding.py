from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

def check_funding():
    h = Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )
    
    # Check specific ARC ID
    res = h.execute_cypher("MATCH (g:Grant {application_id: 'DP0208120'}) RETURN g")
    print(f"ARC record DP0208120: {res}")
    
    # Check any ARC record
    res = h.execute_cypher("MATCH (g:Grant) WHERE g.application_id STARTS WITH 'DP' OR g.application_id STARTS WITH 'LP' RETURN g.application_id, g.funding_body LIMIT 5")
    print(f"ARC sample: {res}")
    
    # Check stats grouped by funding body
    res = h.execute_cypher("MATCH (g:Grant) RETURN g.funding_body as body, count(g) as count")
    print(f"Stats: {res}")

if __name__ == "__main__":
    check_funding()
