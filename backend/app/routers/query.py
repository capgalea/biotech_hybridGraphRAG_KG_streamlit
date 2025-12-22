from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.query_processor import QueryProcessor
from app.utils.neo4j_handler import Neo4jHandler
from app.utils.llm_handler import LLMHandler
from app.config import settings, secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    llm_model: str = "claude-4-5-sonnet"
    enable_search: bool = True

@router.post("/")
def process_query(request: QueryRequest):
    try:
        logger.info(f"Processing query: {request.query} with model {request.llm_model}")
        
        if not secrets:
            logger.error("Secrets not loaded. Please check .env")
            raise HTTPException(status_code=500, detail="Configuration error: Secrets not loaded from .env")

        # Initialize Neo4j Handler
        try:
            neo4j_handler = Neo4jHandler(
                uri=settings["neo4j"]["uri"],
                user=settings["neo4j"]["user"],
                password=settings["neo4j"]["password"],
                database=settings["neo4j"]["database"]
            )
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

        # Map frontend model names to backend expected names
        model_map = {
            "claude-4-5-sonnet": "Claude 4.5 Sonnet",
            "claude-3-5-sonnet": "Claude 3.5 Sonnet",
            "gemini-2-0-flash": "Gemini 2.0 Flash",
            "deepseek-r1": "DeepSeek R1",
            "deepseek-v3": "DeepSeek V3"
        }
        backend_model = model_map.get(request.llm_model, "Claude 4.5 Sonnet")
        
        # Initialize LLM Handler
        try:
            llm_handler = LLMHandler(backend_model, secrets)
        except Exception as e:
            logger.error(f"Failed to initialize LLM Handler: {e}")
            raise HTTPException(status_code=500, detail=f"LLM initialization failed: {str(e)}")
        
        # Initialize QueryProcessor
        processor = QueryProcessor(neo4j_handler, llm_handler) 
        
        # Process the query
        result = processor.process_query(request.query, request.enable_search)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
