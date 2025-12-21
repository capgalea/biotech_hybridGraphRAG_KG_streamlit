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

@router.get("/stats")
async def get_stats():
    try:
        handler = get_neo4j_handler()
        stats = handler.get_database_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schema")
async def get_schema():
    try:
        handler = get_neo4j_handler()
        schema = handler.get_schema()
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/institutions")
async def get_top_institutions(limit: int = 10):
    try:
        handler = get_neo4j_handler()
        institutions = handler.get_top_institutions(limit=limit)
        return institutions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
