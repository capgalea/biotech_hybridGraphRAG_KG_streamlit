from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings
import os
from dotenv import load_dotenv

load_dotenv()

# Manually load settings if needed (as app.config might depend on env vars)
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")

print(f"Connecting to {uri} as {user}")

try:
    h = Neo4jHandler(uri, user, password, "neo4j")
    
    query = """
    MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
    WHERE toLower(r.name) CONTAINS 'glenn king'
    RETURN g.title as title, g.application_id as grant_id, 
           r.name as researcher_name, g.funding_body as funding_body, 
           g.start_year as start_year
    LIMIT 1
    """
    
    print("Running query...")
    results = h.execute_cypher(query)
    print(f"Found {len(results)} results")
    
    for i, res in enumerate(results):
        print(f"\nResult {i}:")
        for k, v in res.items():
            print(f"  {k}: {v}")
            
except Exception as e:
    print(f"Error: {e}")
