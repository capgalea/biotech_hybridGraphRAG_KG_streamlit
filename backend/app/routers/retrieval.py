from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, Any
import io
import pandas as pd
import json
import logging
from app.retrieval_agent.agent import fetch_data
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings
from app.utils.cache import clear_cache


router = APIRouter()
logger = logging.getLogger(__name__)

# Global Status (In-memory for simplicity)
retrieval_status = {
    "is_running": False,
    "message": "Ready"
}

# Temporary storage for fetched data (In-memory dataframe for simplicity, or save/load from file)
# In production, use database or persistent file storage.
# We will use the 'outcomes.csv' file that agent saves.
LATEST_DATA_FILE = "outcomes.csv"

def get_neo4j_handler():
    return Neo4jHandler(
        uri=settings['neo4j']['uri'],
        user=settings['neo4j']['user'],
        password=settings['neo4j']['password']
    )

def update_progress(msg: str):
    retrieval_status["message"] = msg
    logger.info(f"Retrieval Progress: {msg}")

import os
import time

# Global Cache
DATA_CACHE = {}
CACHE_TIMESTAMPS = {}

def load_df_cached(filename: str) -> pd.DataFrame:
    """
    Load dataframe from CSV with caching based on file modification time.
    """
    if not os.path.exists(filename):
        return pd.DataFrame()
        
    file_mtime = os.path.getmtime(filename)
    
    # Check if in cache and file hasn't changed
    if filename in DATA_CACHE and filename in CACHE_TIMESTAMPS:
        if CACHE_TIMESTAMPS[filename] == file_mtime:
            return DATA_CACHE[filename]
            
    # Load and cache
    try:
        logger.info(f"Loading {filename} into memory cache...")
        df = pd.read_csv(filename)
        
        # Robustly handle NaNs
        df = df.fillna("")
        if df.isna().any().any():
            df = df.astype(object).fillna("")
        
        # Strip whitespace from all string columns
        df_obj = df.select_dtypes(['object'])
        df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        
        DATA_CACHE[filename] = df
        CACHE_TIMESTAMPS[filename] = file_mtime
        return df
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return pd.DataFrame()

def run_retrieval_task(nhmrc: bool, arc: bool):
    try:
        retrieval_status["is_running"] = True
        fetch_data(nhmrc=nhmrc, arc=arc, save_files=True, progress_callback=update_progress)
        
        # Clear cache to force reload next time
        DATA_CACHE.clear()
        CACHE_TIMESTAMPS.clear()
        
        update_progress("Retrieval Completed. Data saved locally.")
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        update_progress(f"Error: {e}")
    finally:
        retrieval_status["is_running"] = False

def run_neo4j_load_task():
    """Load data from CSV files into Neo4j database."""
    try:
        retrieval_status["is_running"] = True
        update_progress("Starting Neo4j load...")
        
        handler = get_neo4j_handler()
        
        # Clear existing data first
        update_progress("Clearing existing Neo4j data...")
        handler.clear_database()
        logger.info("Neo4j database cleared")
        
        # Load outcomes.csv
        filepath = os.path.join(settings['data_dir'], "outcomes.csv")
        if os.path.exists(filepath):
            update_progress("Loading combined grants to Neo4j...")
            df = pd.read_csv(filepath)
            handler.load_grants_from_dataframe(df)
            clear_cache()
            logger.info(f"Loaded {len(df)} grants to Neo4j and cleared cache")

        else:
            logger.warning(f"{filepath} not found")
            
        handler.close()
        update_progress("Neo4j load completed successfully")
    except Exception as e:
        logger.error(f"Neo4j load failed: {e}")
        update_progress(f"Neo4j Error: {e}")
    finally:
        retrieval_status["is_running"] = False

@router.post("/start")
async def start_retrieval(background_tasks: BackgroundTasks):
    """Start data retrieval from NHMRC and ARC."""
    if retrieval_status["is_running"]:
        raise HTTPException(status_code=409, detail="Task already running")
    
    background_tasks.add_task(run_retrieval_task, nhmrc=True, arc=True)
    return {"message": "Retrieval started"}

@router.post("/load-neo4j")
async def load_neo4j(background_tasks: BackgroundTasks):
    """Load data from CSV files into Neo4j database (clears existing data first)."""
    if retrieval_status["is_running"]:
        raise HTTPException(status_code=409, detail="Task already running")
    
    background_tasks.add_task(run_neo4j_load_task)
    return {"message": "Neo4j load started"}

@router.get("/status")
def get_status():
    """Get current status of retrieval/load operations."""
    return retrieval_status


@router.get("/data")
def get_data(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = "",
    source: str = Query("combined", regex="^(combined|nhmrc|arc)$")
):
    """
    Read from local CSV for preview/table display.
    """
    filename = "outcomes.csv"
    if source == "nhmrc":
        filename = "nhmrc_processed.csv"
    elif source == "arc":
        filename = "arc_processed.csv"
    
    filepath = os.path.join(settings['data_dir'], filename)

        
    try:
        # Use cached loader
        df = load_df_cached(filepath)
        
        if df.empty:
             return {"data": [], "pagination": {"total": 0}}
        
        # 1. Search Filter
        if search:
            search_lower = search.lower()
            mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(search_lower)).any(axis=1)
            df = df[mask]
            
        # 2. Column Filters (from extra query params)
        # Iterate over all query parameters
        for key in request.query_params.keys():
            if key in ['page', 'limit', 'search', 'source']:
                continue
                
            if key in df.columns:
                values = request.query_params.getlist(key)
                if values:
                    # Filter df where column value is in values
                    # Ensure we compare strings to strings
                    df = df[df[key].astype(str).isin(values)]
            
        total = len(df)
        start = (page - 1) * limit
        end = start + limit
        
        paginated = df.iloc[start:end]
        
        return {
            "data": paginated.to_dict(orient="records"),
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        return JSONResponse(status_code=500, content={"message": f"Error reading data: {e}"})

@router.get("/unique_values")
def get_unique_values(column: str, source: str = Query("combined", regex="^(combined|nhmrc|arc)$")):
    """
    Get distinct filter options for a column from local data for preview.
    """
    filename = "outcomes.csv"
    if source == "nhmrc":
        filename = "nhmrc_processed.csv"
    elif source == "arc":
        filename = "arc_processed.csv"

    filepath = os.path.join(settings['data_dir'], filename)

    try:
        # Use cached loader - still fast because it's in memory
        df = load_df_cached(filepath)
        
        if df.empty or column not in df.columns:
             return {"values": []}

        values = sorted(df[column].dropna().unique().tolist())
        return {"values": values}
    except Exception as e:
        logger.error(f"Error in get_unique_values: {e}")
        return {"values": []}

@router.get("/neo4j_stats")
def get_neo4j_stats():
    """Get stats from the Neo4j graph database."""
    try:
        handler = get_neo4j_handler()
        stats = handler.get_database_stats()
        handler.close()
        return {"status": "ok", "stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/export")
def export_data(format: str = "csv", source: str = Query("combined", regex="^(combined|nhmrc|arc)$")):
    filename = "outcomes.csv"
    if source == "nhmrc":
        filename = "nhmrc_processed.csv"
    elif source == "arc":
        filename = "arc_processed.csv"

    filepath = os.path.join(settings['data_dir'], filename)

    if not os.path.exists(filepath):
         raise HTTPException(status_code=404, detail="No data available to export")
         
    df = pd.read_csv(filepath)
    
    stream = io.BytesIO()
    out_filename = f"{source}_grants"
    media_type = "text/csv"
    
    if format == "csv":
        stream.write(df.to_csv(index=False).encode('utf-8-sig'))
        out_filename += ".csv"
        media_type = "text/csv"
    elif format == "json":
        stream.write(df.to_json(orient="records").encode('utf-8'))
        out_filename += ".json"
        media_type = "application/json"
    elif format == "xlsx":
        try:
             df.to_excel(stream, index=False, engine='openpyxl')
             out_filename += ".xlsx"
             media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        except:
             # Fallback
             stream.write(df.to_csv(index=False).encode('utf-8-sig'))
             out_filename += ".csv"
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
        
    stream.seek(0)
    return StreamingResponse(
        stream, 
        media_type=media_type, 
        headers={"Content-Disposition": f"attachment; filename={out_filename}"}
    )
