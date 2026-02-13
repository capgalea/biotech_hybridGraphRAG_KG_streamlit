from app.utils.neo4j_handler import Neo4jHandler
import os
from dotenv import load_dotenv

load_dotenv()

handler = Neo4jHandler(
    uri=os.getenv("NEO4J_URI"),
    user=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE", "neo4j")
)

# Check 1: Counts for terms
print("--- Counts ---")
query_counts = """
MATCH (g:Grant)
RETURN 
    count(g) as total,
    size([g IN collect(g) WHERE toLower(g.title + coalesce(g.description, '')) CONTAINS 'antibacterial']) as antibacterial,
    size([g IN collect(g) WHERE toLower(g.title + coalesce(g.description, '')) CONTAINS 'resistance']) as resistance,
    size([g IN collect(g) WHERE toLower(g.title + coalesce(g.description, '')) CONTAINS 'antibacterial resistance']) as phrase_match,
    size([g IN collect(g) WHERE toLower(g.title + coalesce(g.description, '')) CONTAINS 'antimicrobial']) as antimicrobial
"""
print(handler.execute_cypher(query_counts))

# Check 2: Monash variants
print("\n--- Monash ---")
query_monash = """
MATCH (i:Institution)
WHERE toLower(i.name) CONTAINS 'monash'
RETURN i.name, count { (i)<-[:HOSTED_BY]-(:Grant) } as grant_count
"""
print(handler.execute_cypher(query_monash))

# Check 3: Mixed
print("\n--- Mixed Search (Manual) ---")
# Finding grants with 'antibacterial' AND 'resistance' but NOT phrase 'antibacterial resistance'
query_debug = """
MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
WHERE 
    (toLower(g.title) CONTAINS 'antibacterial' OR toLower(coalesce(g.description, '')) CONTAINS 'antibacterial')
    AND (toLower(g.title) CONTAINS 'resistance' OR toLower(coalesce(g.description, '')) CONTAINS 'resistance')
    AND NOT (toLower(g.title) CONTAINS 'antibacterial resistance' OR toLower(coalesce(g.description, '')) CONTAINS 'antibacterial resistance')
    AND toLower(i.name) CONTAINS 'monash'
RETURN g.title, i.name
LIMIT 10
"""
res = handler.execute_cypher(query_debug)
print(f"Grants with terms separated: {len(res)}")
for r in res:
    print(r)

handler.close()
