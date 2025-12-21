from fastapi import APIRouter, HTTPException
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

router = APIRouter()

def get_neo4j_handler():
    return Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )

@router.get("/researcher/{name}")
async def get_researcher(name: str):
    try:
        handler = get_neo4j_handler()
        query = """
        MATCH (r:Researcher {name: $researcher_name})
        OPTIONAL MATCH (r)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
        OPTIONAL MATCH (r)-[:AFFILIATED_WITH]->(i:Institution)
        RETURN r.name as researcher_name,
               r.title as title,
               r.department as department,
               r.email as email,
               collect(DISTINCT i.name) as institutions,
               collect(DISTINCT {
                   title: g.title,
                   amount: g.amount,
                   start_date: g.start_date,
                   end_date: g.end_date,
                   agency: g.agency,
                   description: g.description,
                   plain_description: g.plain_description
               }) as grants
        """
        results = handler.execute_cypher(query, {"researcher_name": name})
        if not results:
            raise HTTPException(status_code=404, detail="Researcher not found")
        return results[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
