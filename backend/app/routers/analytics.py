from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

router = APIRouter()

_handler = None

def get_neo4j_handler():
    global _handler
    if _handler is None:
        _handler = Neo4jHandler(
            uri=settings["neo4j"]["uri"],
            user=settings["neo4j"]["user"],
            password=settings["neo4j"]["password"],
            database=settings["neo4j"]["database"]
        )
    return _handler

@router.get("/stats")
@router.get("/stats")
async def get_stats(
    institution: Optional[str] = None,
    start_year: Optional[int] = None,
    grant_type: Optional[str] = None,
    broad_research_area: Optional[str] = None,
    field_of_research: Optional[str] = None,
    funding_body: Optional[str] = None,
    search: Optional[str] = None,
    # New Column Filters
    pi_name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    institution_name: Optional[str] = None,
    grant_status: Optional[str] = None,
    application_id: Optional[str] = None
):
    try:
        handler = get_neo4j_handler()
        filters = {
            "institution": institution,
            "start_year": start_year,
            "grant_type": grant_type,
            "broad_research_area": broad_research_area,
            "field_of_research": field_of_research,
            "funding_body": funding_body,
            "search": search,
            "pi_name": pi_name,
            "title": title,
            "description": description,
            "institution_name": institution_name,
            "grant_status": grant_status,
            "application_id": application_id
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
@router.get("/institutions")
async def get_top_institutions(
    limit: int = 10,
    institution: Optional[str] = None,
    start_year: Optional[int] = None,
    grant_type: Optional[str] = None,
    broad_research_area: Optional[str] = None,
    field_of_research: Optional[str] = None,
    funding_body: Optional[str] = None,
    search: Optional[str] = None,
    # New Column Filters
    pi_name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    institution_name: Optional[str] = None,
    grant_status: Optional[str] = None,
    application_id: Optional[str] = None
):
    try:
        handler = get_neo4j_handler()
        filters = {
            "institution": institution,
            "start_year": start_year,
            "grant_type": grant_type,
            "broad_research_area": broad_research_area,
            "field_of_research": field_of_research,
            "funding_body": funding_body,
            "search": search,
            "pi_name": pi_name,
            "title": title,
            "description": description,
            "institution_name": institution_name,
            "grant_status": grant_status,
            "application_id": application_id
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
    funding_body: Optional[str] = None,
    search: Optional[str] = None,
    # New Column Filters
    pi_name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    institution_name: Optional[str] = None,
    grant_status: Optional[str] = None,
    application_id: Optional[str] = None
):
    try:
        handler = get_neo4j_handler()
        filters = {
            "institution": institution,
            # Trend endpoint typically uses a range, but might filter by exact start year too?
            # It uses start_year_min/max primarily. 
            "grant_type": grant_type,
            "broad_research_area": broad_research_area,
            "field_of_research": field_of_research,
            "funding_body": funding_body,
            "search": search,
            "pi_name": pi_name,
            "title": title,
            "description": description,
            "institution_name": institution_name,
            "grant_status": grant_status,
            "application_id": application_id
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
    # New Column Filters
    pi_name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    institution_name: Optional[str] = None,
    grant_status: Optional[str] = None,
    application_id: Optional[str] = None,
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
            "funding_body": funding_body,
            "pi_name": pi_name,
            "title": title,
            "description": description,
            "institution_name": institution_name,
            "grant_status": grant_status,
            "application_id": application_id
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        # Note: get_grants_list takes `filters` and optional `search`. 
        # But _build_filter_clause handles 'search' if it's in filters.
        # Let's pass search explicitly if the handler expects it, or add to filters.
        # Neo4jHandler.get_grants_list(..., filters=filters, search=search, ...) 
        # If I look at the previous file content (Step 868), line 147:
        # grants = handler.get_grants_list(limit=limit, skip=skip, filters=filters, search=search, sort_by=sort_by, order=order)
        # So I will keep passing search explicitly to match signature, but ALSO add it to filters if needed?
        # Actually, let's check if get_grants_list adds search to filters.
        # If I assume get_grants_list logic:
        # def get_grants_list(self, ..., filters=None, search=None, ...):
        #    if search:
        #        filters['search'] = search
        #    ...
        # So I will just pass it as is.
        grants = handler.get_grants_list(limit=limit, skip=skip, filters=filters, search=search, sort_by=sort_by, order=order)
        return grants
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
