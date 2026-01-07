from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
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
async def get_stats(
    institution: Optional[str] = None,
    start_year: Optional[int] = None,
    grant_type: Optional[str] = None,
    broad_research_area: Optional[str] = None,
    field_of_research: Optional[str] = None,
    funding_body: Optional[str] = None
):
    try:
        handler = get_neo4j_handler()
        filters = {
            "institution": institution,
            "start_year": start_year,
            "grant_type": grant_type,
            "broad_research_area": broad_research_area,
            "field_of_research": field_of_research,
            "funding_body": funding_body
        }
        # Filter out None values
        filters = {k: v for k, v in filters.items() if v is not None}
        stats = handler.get_database_stats(filters=filters)
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
async def get_top_institutions(
    limit: int = 10,
    institution: Optional[str] = None,
    start_year: Optional[int] = None,
    grant_type: Optional[str] = None,
    broad_research_area: Optional[str] = None,
    field_of_research: Optional[str] = None,
    funding_body: Optional[str] = None
):
    try:
        handler = get_neo4j_handler()
        filters = {
            "institution": institution,
            "start_year": start_year,
            "grant_type": grant_type,
            "broad_research_area": broad_research_area,
            "field_of_research": field_of_research,
            "funding_body": funding_body
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        institutions = handler.get_top_institutions(limit=limit, filters=filters)
        return institutions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
async def get_funding_trends(
    start_year_range: int = Query(2000, alias="start_year_min"),
    end_year_range: int = Query(2030, alias="start_year_max"),
    institution: Optional[str] = None,
    grant_type: Optional[str] = None,
    broad_research_area: Optional[str] = None,
    field_of_research: Optional[str] = None,
    funding_body: Optional[str] = None
):
    try:
        handler = get_neo4j_handler()
        filters = {
            "institution": institution,
            "grant_type": grant_type,
            "broad_research_area": broad_research_area,
            "field_of_research": field_of_research,
            "funding_body": funding_body
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        trends = handler.get_funding_trends(start_year=start_year_range, end_year=end_year_range, filters=filters)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filters")
async def get_filters():
    try:
        handler = get_neo4j_handler()
        options = handler.get_filter_options()
        return options
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/grants")
async def get_grants(
    limit: int = 50,
    skip: int = 0,
    institution: Optional[str] = None,
    start_year: Optional[int] = None,
    grant_type: Optional[str] = None,
    broad_research_area: Optional[str] = None,
    field_of_research: Optional[str] = None,
    funding_body: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "start_year",
    order: str = "DESC"
):
    try:
        handler = get_neo4j_handler()
        filters = {
            "institution": institution,
            "start_year": start_year,
            "grant_type": grant_type,
            "broad_research_area": broad_research_area,
            "field_of_research": field_of_research,
            "funding_body": funding_body
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        grants = handler.get_grants_list(limit=limit, skip=skip, filters=filters, search=search, sort_by=sort_by, order=order)
        return grants
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
