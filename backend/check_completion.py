from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

def check_completion():
    h = Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )
    
    # Check total grants
    res = h.execute_cypher("MATCH (g:Grant) RETURN count(g) as total")
    print(f"Total Grants: {res[0]['total']}")
    
    # Check funding body distribution
    res = h.execute_cypher("MATCH (g:Grant) RETURN g.funding_body as body, count(g) as count ORDER BY count DESC")
    print(f"\nFunding Body Distribution:")
    for row in res:
        print(f"  {row['body']}: {row['count']}")
    
    # Check other stats
    res = h.execute_cypher("MATCH (r:Researcher) RETURN count(r) as total")
    print(f"\nTotal Researchers: {res[0]['total']}")
    
    res = h.execute_cypher("MATCH (i:Institution) RETURN count(i) as total")
    print(f"Total Institutions: {res[0]['total']}")

if __name__ == "__main__":
    check_completion()
