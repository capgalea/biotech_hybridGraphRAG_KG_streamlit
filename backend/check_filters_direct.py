from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

def check_filters_direct():
    h = Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )
    
    # Get funding bodies directly from database
    res = h.execute_cypher("MATCH (g:Grant) WHERE g.funding_body IS NOT NULL RETURN DISTINCT g.funding_body as body ORDER BY body")
    print("=== Funding Bodies in Database ===")
    funding_bodies = [row['body'] for row in res]
    for body in funding_bodies:
        print(f"  ✓ {body}")
    
    print(f"\nTotal: {len(funding_bodies)} funding bodies")
    
    # Verify count for each
    print("\n=== Grant Counts by Funding Body ===")
    res = h.execute_cypher("MATCH (g:Grant) RETURN g.funding_body as body, count(g) as count ORDER BY body")
    for row in res:
        print(f"  {row['body']}: {row['count']:,} grants")

if __name__ == "__main__":
    check_filters_direct()
